#!/usr/bin/env python
#
# Copyright 2011-2013 Splunk, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"): you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import random
import csv
import sys
import time

from splunklib.searchcommands import \
    dispatch, GeneratingCommand, Configuration, Option, validators


@Configuration()
class SimulateCommand(GeneratingCommand):
    """ Generates a sequence of events drawn from a CSV file using repeated
    random sampling

    ##Syntax

    simulate csv=<path> rate=<expected-event-count> interval=<sampling-period>
        duration=<execution-period> [seed=<string>]

    ##Description

    The `simulate` command uses repeated random samples of the event records
    in `csv` for the execution period of `duration`. Samples sizes are
    determined for each time `interval` in `duration` using a Poisson
    distribution with an average `rate` specifying the expected event count
    during `interval`.

    ##Example

    ```
    | simulate csv=population.csv rate=200 interval=00:00:01 duration=00:00:30 |
    countmatches fieldname=word_count pattern="\\w+" text |
    stats mean(word_count) stdev(word_count)
    ```

    This example generates events drawn from repeated random sampling of events
    from `tweets.csv`. Events are drawn at an average rate of 200 events per
    second for a duration of 30 seconds. Events are piped to the example
    `countmatches` command which adds a `word_count` field containing the number
    of words in the `text` field of each event. The mean and standard deviation
    of the `word_count` are then computed by the builtin `stats` command.


    """
    csv_file = Option(
        doc='''**Syntax:** **csv=***<path>*
        **Description:** CSV file from which repeated random samples will be
        drawn''',
        name='csv', require=True, validate=validators.File())

    duration = Option(
        doc='''**Syntax:** **duration=***<time-interval>*
        **Description:** Duration of simulation''',
        require=True, validate=validators.Duration())

    interval = Option(
        doc='''**Syntax:** **interval=***<time-interval>*
        **Description:** Sampling interval''',
        require=True, validate=validators.Duration())

    rate = Option(
        doc='''**Syntax:** **rate=***<expected-event-count>*
        **Description:** Average event count during sampling `interval`''',
        require=True, validate=validators.Integer(1))

    seed = Option(
        doc='''**Syntax:** **seed=***<string>*
        **Description:** Value for initializing the random number generator ''')

    def generate(self):
        """ Yields one random record at a time for the duration of `duration` """
        self.logger.debug('SimulateCommand: %s' % self)  # log command line
        if not self.records:
            if self.seed is not None:
                random.seed(self.seed)
            self.records = [record for record in csv.DictReader(self.csv_file)]
            self.lambda_value = 1.0 / (self.rate / float(self.interval))
        duration = self.duration
        while duration > 0:
            count = long(round(random.expovariate(self.lambda_value)))
            start_time = time.clock()
            for record in random.sample(self.records, count):
                yield record
            interval = time.clock() - start_time
            if interval < self.interval:
                time.sleep(self.interval - interval)
            duration -= max(interval, self.interval)
        return

    def __init__(self):
        super(SimulateCommand, self).__init__()
        self.lambda_value = None
        self.records = None

dispatch(SimulateCommand, sys.argv, sys.stdin, sys.stdout, __name__)
