#!/usr/bin/env python
# encoding: utf-8
"""
ALTactileGesture.py

Created by Aldebaran Boston Studio.
"""
import qi
import threading
import operator as op
import logging as logger


class Gesture:
    """ Class: Gesture

    Internal class to help in processing of gestures.
    """
    def __init__(self, name, sequence):
        self.name = name
        self.sequence = sequence
        self.hold = True if sequence[-1] != 0 else False


@qi.multiThreaded()
class ALTactileGesture:
    """Class: ALTactileGesture

    Service that allows advanced touch head-sensor events to be
    detected and used by other apps via  qi.signals. Included
    gestures fire the following signal:

            - onGesture

    Hold events will repeat until the hold is released or until the sensor
    determines it has been touched for long enough (about 40s)

    IMPORTANT: ALTactileGesture module is based on qimessaging, therefore
    session.service must be used (instead of ALProxy).

    For those in need of old-style ALMemory events, you can use this:

            - ALTactileGesture/Gesture
    """

    def __init__(self, session):
        self.session = session
        logger.basicConfig(filename='ALTactileGesture.log', level=logger.DEBUG)
        self.logger = logger

        self.is_running = False
        self.module_name = 'ALTactileGesture'

        # Locks
        self.sensor_change = False
        self.sensor_lock = threading.Lock()

        # Timers
        self.s_to_micros = 1000000
        # Time from initial sensor signal to measurement of all sensors
        # (settling time)
        self.e_sim = int(0.04*self.s_to_micros)
        # Time from sensor measurement to 'hold' status
        # (hold time)
        self.d_hold = int(0.8*self.s_to_micros)
        # Time allowed from sensor measurement to next signal to be linked as
        # (sequence time)
        self.e_seq = int(0.2*self.s_to_micros)
        self.e_sim_future = None
        self.d_hold_future = None
        self.e_seq_future = None

        # Build a list of devices with full name
        self.device_names = ['{}TactilTouched'.format(sen) for sen in ['Rear', 'Middle', 'Front']]
        self.subscriptions = []

        # Parameters
        # Note: Below are head sensor touch sequence encoded as binary
        # representations of the three head sensors in Front, Middle, Rear order
        gestures = {
            'SingleFront': [0b000, 0b100, 0b000],
            'SingleMiddle': [0b000, 0b010, 0b000],
            'SingleRear': [0b000, 0b001, 0b000],
            'DoubleFront': [0b000, 0b100, 0b000, 0b100, 0b000],
            'DoubleMiddle': [0b000, 0b010, 0b000, 0b010, 0b000],
            'DoubleRear': [0b000, 0b001, 0b000, 0b001, 0b000],
            'SingleTap': [0b000, 0b111, 0b000],
            'DoubleTap': [0b000, 0b111, 0b000, 0b111, 0b000],
            'CaressFtoR': [0b000, 0b100, 0b010, 0b001, 0b000],
            'CaressRtoF': [0b000, 0b001, 0b010, 0b100, 0b000],
            'ZoomIn': [0b000, 0b101, 0b010, 0b000],
            'ZoomOut': [0b000, 0b010, 0b101, 0b000],
            'SecretCode': [0b000, 0b101, 0b000, 0b101, 0b010, 0b000],
            'TheClaw': [0b000, 0b101, 0b000],
            # Holds
            # Note: Hold sequences must not end in '000'
            'SingleFrontHold': [0b000, 0b100],
            'SingleMiddleHold': [0b000, 0b010],
            'SingleRearHold': [0b000, 0b001],
            'SingleTapHold': [0b000, 0b111],
            'TheClawHold': [0b000, 0b101]
        }

        # Init services
        self._connect_services()

        # Init Signals
        self._sync_preferences()
        self.all_gestures = [Gesture(k, v) for k, v in gestures.iteritems()]
        self._connect_signals()

        # Init sequence
        self.active_sequence = [0b000]
        self.active_hold = False
        self.last_sensor_state = None

        # Running process variables
        self.is_running = False

        self._start()

    def _connect_services(self):
        """Connect to all services required by ALTactileGesture"""
        self.services_connected = qi.Promise()
        services_connected_fut = self.services_connected.future()

        def get_services():
            """Attempt to get all services"""
            try:
                self.memory = self.session.service('ALMemory')
                self.prefs = self.session.service('ALPreferenceManager')
                self.logger.info('got references to all services')
                self.services_connected.setValue(True)
            except RuntimeError as e:
                self.logger.warning('missing service:\n {}'.format(e))

        get_services_task = qi.PeriodicTask()
        get_services_task.setCallback(get_services)
        get_services_task.setUsPeriod(int(2*1000000))  # check every 2s
        get_services_task.start(True)

        try:
            services_connected_fut.value(30*1000)  # timeout = 30s
            get_services_task.stop()
        except RuntimeError:
            get_services_task.stop()
            self.logger.info('Failed to reach all services after 30 seconds')
            raise RuntimeError

    def _connect_signals(self):
        """Init qi.Signals and memory events (for compatibility)"""
        self.onGesture = qi.Signal()
        self.onRelease = qi.Signal()
        self.gestureEvent = '{}/{}'.format(self.module_name, 'Gesture')
        self.releaseEvent = '{}/{}'.format(self.module_name, 'Release')
        self.memory.declareEvent(self.gestureEvent, self.module_name)
        self.memory.declareEvent(self.releaseEvent, self.module_name)

    def _on_sensor_change(self, value):
        """
        On any head sensor change, acquire lock and starts e_sim (settling)
        timer.
        Note: Only the first signal starts the timer and all others are
        debounced.
        """
        locked = self.sensor_lock.acquire(False)
        if locked:
            self._start_e_sim_timer()

    def _read_sensors(self):
        """
        Once the settling time (e_sim) is over:
          - Read from head sensors.
          - Store pattern
          - Start hold and sequential timers
        """
        # Get sensor values and convert None into 0 when necessary
        sensor_list = self.memory.getListData(self.device_names)
        raw_sensors = [0 if s is None else int(s) for s in sensor_list]
        sensor_state = 0
        # Convert sensor state to integer
        for i, b in enumerate(raw_sensors):
            sensor_state += (b << i)
        # Only act upon signal if the state of the sensors has changed
        if sensor_state != self.last_sensor_state:
            self.sensor_change = True
            self.active_sequence.append(sensor_state)
            self.last_sensor_state = sensor_state
            self._cancel_futures()
            # Start hold timer if any sensor is active
            if sensor_state:
                self._start_d_hold_timer()
            # Otherwise start sequence timer
            else:
                self._start_e_seq_timer()
        else:
            self.sensor_change = False
        self.sensor_lock.release()

    def _eval_hold(self):
        """
        Once the hold time has expired:
          - Evaluate if the current sequence is a valid hold gesture
          - Fire gesture signal (if valid)
          - Reset for next touch input
        """
        self.sensor_change = False
        if self.sensor_lock.acquire():
            if not self.sensor_change:
                self.active_hold = True
                gesture = self._search_gestures()
                if gesture:
                    self._fire_gesture_signal(gesture)
            self._clean_up_hold()
            self.sensor_lock.release()

    def _eval_sequence(self):
        """
        Once the sequence time has expired:
          - Evaluate if the current sequence is a valid gesture
          - Fire gesture signal (if valid)
          - Reset for next touch input
        """
        self.sensor_change = False
        if self.sensor_lock.acquire():
            if not self.sensor_change:
                gesture = self._search_gestures()
                if gesture:
                    self._fire_gesture_signal(gesture)
            self._fire_release_signal()
            self._clean_up()
            self.sensor_lock.release()

    def _search_gestures(self):
        """
        Compare inputted sequence to all gestures to find match

        Algorithm:
        1. async call _check_sequence on for all gestures
           (i.e. gestures that match the current hold status and are not unset custom gestures)
              -> _check_sequence() will fullfill promise with the gesture if matched; else None
        2. Build list of all futures whose value is a matched sequence
        3. Return the gesture whose match is the closest the sequence prototype
           it matched (i.e. smallest difference)
        """
        futures = []
        las = len(self.active_sequence)
        # For every sequence; start check asynchronously
        for gesture in self.all_gestures:
            if gesture.hold == self.active_hold:
                p = qi.Promise()
                futures.append(p.future())
                qi.async(self._check_sequence, self.active_sequence, las, gesture, p)
        # Walks through futures list; waits on each promise to be fullfiled
        vf = (f.value() for f in futures if f.value()[0])
        # Returns gesture corresponding to min diff value in vf above
        # If vf is empty, returns (None, 0)
        return reduce(lambda x, y: min((x, y), key=op.itemgetter(1)),
                      vf, next(vf, (None, 0)))[0]

    def _check_sequence(self, a_s, las, gesture, promise):
        """
        Given a gesture, check if the active sequence matches it.

        Algorithm:
        1. Create a list of overlapping pairs from each gesture's sequence
        2. Loop through each pair (a,b):
           3. If the active sequence matches 'a' in the pair:
              4. Check if the active sequence contains the 'b' in the pair
                 5a. If True, check if it is within n-1 positions from where 'a'
                     was (Where 'n' is the number of bits changed between 'a'
                     and 'b')
                     6a. If True: goto Step 2 [if last pair; goto Step 7)
                     6b. Else: break; fullfill promise as None
                 5b. Else: break; fullfill promise as None
        7. If all pairs check out and they used all of the active sequence
           8. Fullfill promise with the gesture and the difference in length between the
              inputted sequence and the matched sequence (i.e. the number of
              excess frames)
        """
        gs = gesture.sequence
        lss = len(gs)
        # Create overlapping list of pairs
        p_seq = [(x, y) for x, y in zip(gs, gs[1:])]
        idx = 0
        idx_peek = 0
        # Walk through each pair
        for seq_tup in p_seq:
            valid = False
            # Make sure current position in a_s matches first item in pair
            if a_s[idx] == seq_tup[0]:
                try:
                    # Attempt to find second element of pair in a_s
                    idx_peek = a_s[idx:].index(seq_tup[1])
                    # Make sure it's within n-1 positions from first item in
                    # pair
                    if idx_peek <= self._bit_distance(seq_tup):
                        valid = True
                        # Update position in a_s
                        idx += idx_peek
                    else:
                        break
                except ValueError:
                    break
        # Validate that the match is proper (i.e. used all of a_s)
        if valid and idx == (las - 1):
            promise.setValue((gesture, las - lss))
            return
        # If not a match...
        promise.setValue((None, 0))

    def _bit_distance(self, pair):
        """
        Computes 'Hamming distance' between the binary representations of
        numbers in pair
        """
        i = pair[0] ^ pair[1]
        count = 0
        while i:
            i &= i - 1
            count += 1
        return count

    def _fire_gesture_signal(self, gesture):
        """Fire signal linked to gesture"""
        self.onGesture(gesture.name)
        # Raise ALMemory event for legacy support
        self.memory.raiseEvent(self.gestureEvent, gesture.name)
        qi.async(self.memory.removeData, self.gestureEvent, delay=self.s_to_micros)

    def _fire_release_signal(self):
        """Fire signal linked to release of sensors"""
        self.onRelease()
        # Raise ALMemory event for legacy support
        self.memory.raiseEvent(self.releaseEvent, 1)
        qi.async(self.memory.removeData, self.releaseEvent, delay=self.s_to_micros)

    def _clean_up(self):
        """Clean up/reset after a sequence has been completed"""
        self._cancel_futures()
        self.active_sequence = [0b000]
        self.active_hold = False
        self.sensor_change = False

    def _clean_up_hold(self):
        """Clean up/reset after a hold sequence has been completed"""
        self._cancel_futures()
        self._start_d_hold_timer()
        self.active_hold = True
        self.sensor_change = False

    def _start_e_sim_timer(self):
        """Starts timer that waits for a setteling time before reading the sensors"""
        try:
            self.e_sim_future = qi.async(self._read_sensors, delay=self.e_sim)
        except RuntimeError as re:
            self.logger.warning('Error in starting settling timer: {}'.format(re))

    def _start_d_hold_timer(self):
        """Starts a timer that waits for the hold period to evaluate if there is a
        valid hold sequence"""
        try:
            self.d_hold_future = qi.async(self._eval_hold, delay=self.d_hold)
        except RuntimeError as re:
            self.logger.warning('Error in starting hold timer: {}'.format(re))

    def _start_e_seq_timer(self):
        """Starts a timer that determines if events in a sequence happen soon
        enough for them to be considered in teh current sequence."""
        try:
            self.e_seq_future = qi.async(self._eval_sequence, delay=self.e_seq)
        except RuntimeError as re:
            self.logger.warning('Error in starting sequence timer: {}'.format(re))

    def _cancel_futures(self):
        """Cancel all futures"""
        try:
            if self.e_sim_future:
                self.e_sim_future.cancel()
        except RuntimeError as re:
            self.logger.warning('Error in stopping settling future: {}'.format(re))
        try:
            if self.d_hold_future:
                self.d_hold_future.cancel()
        except RuntimeError as re:
            self.logger.warning('Error in stopping hold future: {}'.format(re))
        try:
            if self.e_seq_future:
                self.e_seq_future.cancel()
        except RuntimeError as re:
            self.logger.warning('Error in stopping sequence future: {}'.format(re))

    def _start(self):
        """Start subscriptions to head sensors"""
        if not self.is_running:
            self.is_running = True
            # Subscribe to each sensor device
            for device in self.device_names:
                subs = self.memory.subscriber(device)
                subs_id = subs.signal.connect(self._on_sensor_change)
                self.subscriptions.append((subs, subs_id))

    def _stop(self):
        """Unsubscribe from head sensors"""
        if self.is_running:
            for subs in self.subscriptions:
                subs[0].signal.disconnect(subs[1])
            self.is_running = False

    # ############################## #
    # ############################## #
    # #### APIs and Preferences #### #
    # ############################## #
    # ############################## #

    def _sync_preferences(self):
        """Sync with preferences. This includes: Settle Time, Hold Time and Sequence Time"""
        self.logger.info('Syncing preferences...')
        # Sync Timing Preferences
        settle_time = self.prefs.getValue(self.module_name, 'SettleTime')
        if settle_time:
            self._set_settle_time(float(settle_time))
            self.logger.info('Syncing settle time...')
        hold_time = self.prefs.getValue(self.module_name, 'HoldTime')
        if hold_time:
            self._set_hold_time(float(hold_time))
            self.logger.info('Syncing hold time...')
        sequence_time = self.prefs.getValue(self.module_name, 'SequenceTime')
        if sequence_time:
            self._set_sequence_time(float(sequence_time))
            self.logger.info('Syncing sequence time...')

    @qi.bind(returnType=qi.String, paramsType=(qi.String,),
             methodName='createGesture')
    def create_gesture_string(self, sensor_sequence):
        """Define touch gesture.

        :param sensor_sequence: Comma-separated string that represents
        the sequence of the desired gesture. For example, SingleFront
        would be the following: "000,100,000". NOTE: All sequences
        must start with '000' and all non-hold sequences must end with
        '000'. Hold gestures should end with the touch sequence you
        will be holding. For example, a SingleFrontHold would be the
        following: "000,100".

        :returns: If sequence is valid, the name of gesture to listen
        for, RuntimeError otherwise."""
        gs = sensor_sequence.split(',')
        return self.create_gesture_list(gs)

    @qi.bind(returnType=qi.String, paramsType=(qi.List(qi.String),),
             methodName='createGesture')
    def create_gesture_list(self, sensor_sequence):
        """Define touch gesture.

        :param sensor_sequence: List of strings that represent the
        sequence of the desired gesture. For example, SingleFront
        would be the following: ['000', '100', '000']. NOTE: All
        sequences must start with '000' and all non-hold sequences
        must end with '000'. Hold gestures should end with the touch
        sequence you will be holding. For example, a SingleFrontHold
        would be the following: ['000', '100'].

        :returns: If sequence is valid, the name of gesture to listen
        for, RuntimeError otherwise."""
        if self.sensor_lock.acquire():
            self._cancel_futures()
            valid_seq = self._validate_sequence(sensor_sequence)
            if valid_seq:
                existing_seq = None
                for gesture in self.all_gestures:
                    if gesture.sequence == valid_seq:
                        existing_seq = gesture.name

                if not existing_seq:
                    gesture_name = self._create_gesture_name(valid_seq)
                    gesture = Gesture(gesture_name, valid_seq)
                    self.all_gestures.append(gesture)

            self._clean_up()
            self.sensor_lock.release()

            if not valid_seq:
                raise RuntimeError('Invalid gesture sequence. Malformed.')
            else:
                return gesture_name if not existing_seq else existing_seq

    def _create_gesture_name(self, sequence):
        """Create gesture name from sequence"""
        return 'gesture-' + ''.join(str(n) for n in sequence)

    def _validate_sequence(self, sensor_sequence):
        """Validate a requested gesture sequence"""
        new_seq = []
        valid = False
        lns = len(sensor_sequence)
        if lns < 2:
            return None

        for idx, seq in enumerate(sensor_sequence):
            valid = False
            try:
                iseq = int(seq, 2)
            except ValueError:
                break
            if iseq > 7 or iseq < 0:
                break
            if idx == 0 and iseq != 0:
                break
            valid = True
            new_seq.append(iseq)

        return new_seq if valid else None

    @qi.bind(returnType=qi.List(qi.String), paramsType=(qi.String,), methodName='getSequence')
    def get_sequence(self, gesture_name):
        """Get the sequence associated with a gesture name

        :param gesture_name: Name of gesture you want the sequence of

        :returns: Sequence (as list of strings) if it exists, None otherwise
        """
        for gesture in self.all_gestures:
            if gesture_name == gesture.name:
                return ['{0:03b}'.format(s) for s in gesture.sequence]
        return None

    @qi.bind(paramsType=(qi.String,), methodName='getGesture')
    def get_gesture_string(self, sequence):
        """Get the sequence associated with a gesture name

        :param sequence: Sequence you want the gesture name of

        :returns: Sequence (as list of strings) if it exists, None otherwise"""
        gs = sequence.split(',')
        return self.get_gesture_list(gs)

    @qi.bind(paramsType=(qi.List(qi.String),), methodName='getGesture')
    def get_gesture_list(self, sequence):
        """Get the sequence associated with a gesture name

        :param sequence: Sequence you want the gesture name of

        :returns: Sequence (as list of strings) if it exists, None otherwise"""
        try:
            c_seq = [int(x, 2) for x in sequence]
        except (TypeError, ValueError):
            return None
        for gesture in self.all_gestures:
            if c_seq == gesture.sequence:
                return gesture.name
        return None

    @qi.bind(returnType=qi.Map(qi.String, qi.List(qi.String)), methodName='getGestures')
    def get_gestures(self):
        """Get all gestures that have been defined in the system

        :returns: Dictionary (Map<String, List<String>>) of all gestures"""
        return {gesture.name: ['{0:03b}'.format(s) for s in gesture.sequence]
                for gesture in self.all_gestures}

    @qi.bind(returnType=qi.Bool, paramsType=(qi.String,), methodName='setSettleTime')
    def set_settle_time_string(self, settle_time):
        """Update length of settling time.

        :param settle_time: Desired settling time, in seconds (Default: 0.04s)

        :returns: True if settle time successfully updated, RuntimeError otherwise."""
        settle_time = float(settle_time)
        return self.set_settle_time(settle_time)

    @qi.bind(returnType=qi.Bool, paramsType=(qi.Float,), methodName='setSettleTime')
    def set_settle_time(self, settle_time):
        """Update length of settling time.

        :param settle_time: Desired settling time, in seconds (Default: 0.04s)

        :returns: True if settle time successfully updated, RuntimeError otherwise."""
        if self.sensor_lock.acquire():
            self._cancel_futures()
            set = self._set_settle_time(settle_time)
            self._clean_up()
            self.sensor_lock.release()
            if not set:
                raise RuntimeError('Invalid time value.')
            return set

    def _set_settle_time(self, settle_time):
        try:
            self.e_sim = int(settle_time*self.s_to_micros)
            return True
        except ValueError:
            return False

    @qi.bind(returnType=qi.Bool, paramsType=(qi.String,), methodName='setHoldTime')
    def set_hold_time_string(self, hold_time):
        """Set length of hold time.

        :param hold_time: Desired hold time, in seconds (Default: 0.8s)

        :returns: True if hold time successfully updated, RuntimeError otherwise."""
        hold_time = float(hold_time)
        return self.set_hold_time(hold_time)

    @qi.bind(returnType=qi.Bool, paramsType=(qi.Float,), methodName='setHoldTime')
    def set_hold_time(self, hold_time):
        """Set length of hold time.

        :param hold_time: Desired hold time, in seconds (Default: 0.8s)

        :returns: True if hold time successfully updated, RuntimeError otherwise."""
        if self.sensor_lock.acquire():
            self._cancel_futures()
            set = self._set_hold_time(hold_time)
            self._clean_up()
            self.sensor_lock.release()
            if not set:
                raise RuntimeError('Invalid time value.')
            return set

    def _set_hold_time(self, hold_time):
        try:
            self.d_hold = int(hold_time*self.s_to_micros)
            return True
        except ValueError:
            return False

    @qi.bind(returnType=qi.Bool, paramsType=(qi.String,), methodName='setSequenceTime')
    def set_sequence_time_string(self, sequence_time):
        """Set length of sequence time.

        :param sequence_time: Desired sequence time, in seconds (Default: 0.2s)

        :returns: True if sequence time successfully updated, RuntimeError otherwise."""
        sequence_time = float(sequence_time)
        return self.set_sequence_time(sequence_time)

    @qi.bind(returnType=qi.Bool, paramsType=(qi.Float,), methodName='setSequenceTime')
    def set_sequence_time(self, sequence_time):
        """Update length of sequence time.

        :param sequence_time: Desired sequence time, in seconds (Default: 0.2s)

        :returns: True if sequence time successfully updated, RuntimeError otherwise."""
        if self.sensor_lock.acquire():
            self._cancel_futures()
            set = self._set_sequence_time(sequence_time)
            self._clean_up()
            self.sensor_lock.release()
            if not set:
                raise RuntimeError('Invalid time value.')
            return set

    def _set_sequence_time(self, sequence_time):
        try:
            self.e_seq = int(sequence_time*self.s_to_micros)
            return True
        except ValueError:
            return False


def register_as_service(service_class, robot_ip="127.0.1"):
    """
    Registers a service in naoqi
    """
    session = qi.Session()
    session.connect("tcp://%s:9559" % robot_ip)
    service_name = service_class.__name__
    instance = service_class(session)
    try:
        session.registerService(service_name, instance)
        print 'Successfully registered service: {}'.format(service_name)
    except RuntimeError:
        print '{} already registered, attempt re-register'.format(service_name)
        for info in session.services():
            try:
                if info['name'] == service_name:
                    session.unregisterService(info['serviceId'])
                    print "Unregistered {} as {}".format(service_name,
                                                         info['serviceId'])
                    break
            except (KeyError, IndexError):
                pass
        session.registerService(service_name, instance)
        print 'Successfully registered service: {}'.format(service_name)


def main():
    """
    Registers ALTactileGesture as a naoqi service.
    """
    register_as_service(ALTactileGesture)
    app = qi.Application()
    app.run()

if __name__ == "__main__":
    main()
