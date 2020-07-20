#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under the terms of the MIT license.
#
# This program is a black_hole_solver demo

from black_hole_solver import BlackHoleSolver

from six import print_


def main():
    solver = BlackHoleSolver()
    pysolfc_5_black_hole_deal = """
Foundations: AS
AH KC 9D
8S 3H KS
2D KD QD
QS 5H 4H
4C 6S AC
9H 8D 2H
2S TD TC
3D 7S TH
5C JD 6D
9C 7H 6H
KH 8H 6C
4D JH QC
2C JC JS
3C 7D 9S
4S 5S AD
3S QH 7C
5D 8C TS
    """
    solver.read_board(
        board=pysolfc_5_black_hole_deal,
        game_type='black_hole',
        place_queens_on_kings=True,
        wrap_ranks=True)
    assert solver.resume_solution() == solver.BLACK_HOLE_SOLVER__SUCCESS
    m = solver.get_next_move()
    while m:
        print_("Move card in column No. {}".format(m.get_column_idx()))
        m = solver.get_next_move()


main()
