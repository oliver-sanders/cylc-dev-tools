#!/usr/bin/env python3
#
# THIS FILE IS PART OF THE CYLC SUITE ENGINE.
# Copyright (C) NIWA & British Crown (Met Office) & Contributors.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Usage:
    cylc graph SUITE [START] [STOP]

Implement the old ``cylc graph --reference command`` for producing a textural
graph of a suite.

"""

import json

from cylc.flow.config import SuiteConfig
from cylc.flow.cycling.loader import get_point
from cylc.flow.exceptions import SuiteServiceFileError
from cylc.flow.option_parsers import CylcOptionParser as COP
from cylc.flow.suite_files import get_suite_rc
from cylc.flow.templatevars import load_template_vars
from cylc.flow.terminal import cli_function


def get_cycling_bounds(config, start_point=None, stop_point=None):
    """Determine the start and stop points for graphing a suite."""
    # default start and stop points to values in the visualization section
    if not start_point:
        start_point = config.cfg['visualization']['initial cycle point']
    if not stop_point:
        viz_stop_point = config.cfg['visualization']['final cycle point']
        if viz_stop_point:
            stop_point = viz_stop_point

    # don't allow stop_point before start_point
    if stop_point is not None:
        if get_point(stop_point) < get_point(start_point):
            # NOTE: we need to cast with get_point for this comparison due to
            #       ISO8061 extended datetime formats
            stop_point = start_point
        else:
            stop_point = stop_point
    else:
        stop_point = None

    return start_point, stop_point


def get_metrics(config, start_point=None, stop_point=None, ungrouped=False,
                show_suicide=False):
    """Implement ``cylc-graph --reference``."""
    ret = {}

    # get graph
    start_point, stop_point = get_cycling_bounds(
        config, start_point, stop_point)
    graph = config.get_graph_raw(
        start_point, stop_point, ungroup_all=ungrouped)
    if not graph:
        return

    edges = [
        (left, right)
        for left, right, _, suicide, _ in graph
        if right
        if show_suicide or not suicide
    ]
    ret['edges'] = len(edges)

    edge_count = {
        left: 0
        for left, _ in edges
    }
    for left, _ in edges:
        edge_count[left] += 1
    ret['average num dependencies'] = (
        sum(edge_count.values()) / len(edge_count)
    )
    ret['max num dependencies'] = max(edge_count.values())

    nodes = [
        node
        for left, right, _, suicide, _ in graph
        for node in (left, right)
        if node
        if show_suicide or not suicide
    ]
    ret['nodes'] = len(nodes)
    return ret


def get_config(suite, opts, template_vars=None):
    """Return a SuiteConfig object for the provided reg / path."""
    try:
        suiterc = get_suite_rc(suite)
    except SuiteServiceFileError:
        # could not find suite, assume we have been given a path instead
        suiterc = suite
        suite = 'test'
    return SuiteConfig(suite, suiterc, opts, template_vars=template_vars)


def get_option_parser():
    """CLI."""
    parser = COP(
        __doc__, jset=True, prep=True,
        argdoc=[
            ('[SUITE]', 'Suite name or path'),
            ('[START]', 'Initial cycle point '
             '(default: suite initial point)'),
            ('[STOP]', 'Final cycle point '
             '(default: initial + 3 points)')])

    parser.add_option(
        '--icp', action='store', default=None, metavar='CYCLE_POINT', help=(
            'Set initial cycle point. Required if not defined in suite.rc.'))

    return parser


@cli_function(get_option_parser)
def main(parser, opts, suite=None, start=None, stop=None):
    """Implement ``cylc graph``."""
    template_vars = load_template_vars(
        opts.templatevars, opts.templatevars_file)

    config = get_config(suite, opts, template_vars=template_vars)
    ret = get_metrics(
        config,
        start,
        stop,
        ungrouped=True,
        show_suicide=True
    )
    print(
        json.dumps(
            ret,
            indent=4
        )
    )


if __name__ == '__main__':
    main()
