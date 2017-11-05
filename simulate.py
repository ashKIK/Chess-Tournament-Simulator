#!/usr/bin/env python3
import random, collections
from math import *
import combine

simulation_count = 100000

# engine_name(s)
Stockfish = "Stockfish"
Komodo = "Komodo"


def calc_tiebreak(points, crash, result_dict):
  tb = {}
  for name in result_dict:
    for color, name2, score in result_dict[name]:
      l = tb.get(name, [0] * 6)
      l[1] += points[name2] * score
      if color == "B":
        l[2] += 1
        if score == 1:
          l[4] += 1
      if score == 1:
        l[3] += 1
      tb[name] = l
    tb[name][0] = crash[name]
    tb[name][-1] = random.random()
  return tb


def read_elo(filename="ratings.txt"):
  now, full = combine.read_ratings(filename)
  now, full = combine.convert2table(now)
  velo = {}
  vStdDev = {}
  for row in now:
    name = row[1].strip()
    if name == "Name":
      continue
    velo[name] = int(row[2])
    vStdDev[name] = int(row[3])
  return velo, vStdDev


# from BayesElo
eloAdvantage = 32.8
eloDraw = 97.3

fNextGaussian = 0


def NextGaussian():
  global fNextGaussian, NextGaussianValue
  if fNextGaussian:
    fNextGaussian = 0
    return NextGaussianValue
  else:
    fNextGaussian = 1
    while True:
      x = 2 * random.random() - 1
      y = 2 * random.random() - 1
      n2 = x * x + y * y
      if not (n2 >= 1 or n2 == 0):
        break
  m = sqrt(-2 * log(n2) / n2)
  NextGaussianValue = y * m
  return x * m


def init_veloRandom():
  veloRandom = {}
  for name in velo:
    veloRandom[name] = velo[name] + NextGaussian() * vStdDev[name]
  return veloRandom


def Probability(eloDelta):
  return 1 / (1 + pow(10.0, eloDelta / 400.0))


def WinProbability(eloDelta):
  return Probability(-eloDelta - eloAdvantage + eloDraw)


def LossProbability(eloDelta):
  return Probability(eloDelta + eloAdvantage + eloDraw)


def simulate(white, black):
  eloDelta = veloRandom[white] - veloRandom[black]
  xWin = WinProbability(eloDelta)
  xLoss = xWin + LossProbability(eloDelta)
  x = random.random()
  if x < xWin:
    return ["1"]
  elif x < xLoss:
    return ["0"]
  return ["1/2"]


if __name__ == "__main__":
  velo, vStdDev = read_elo()
  pos_dict = {name: collections.Counter() for name in velo}
  win, draw, lost = 0, 0, 0
  for i in range(simulation_count):
    veloRandom = init_veloRandom()
    points = collections.Counter()
    crash = collections.Counter()
    result_dict = {}
    for line in open("schedule.txt"):
      if line.startswith("Schedule"):
        continue
      elif line.startswith(" Nr"):
        white_start = 4
        white_end = line.find("White") + 5
        black_start = line.find("Black")
        black_end = line.find("Termination")
        termination_start = black_end
        termination_end = line.find("Mov")
      else:
        white = line[white_start:white_end].strip()
        black = line[black_start:black_end].strip()
        result = line[white_end:black_start].strip().split()
        termination = line[termination_start:termination_end].strip()
        if termination in (
            "", "TB position", "TCEC win rule", "3-fold repetition", "TCEC draw rule", "Fifty moves rule",
            "in progress"):
          pass
        elif termination in ("White disconnects", "White's connection stalls"):
          crash[white] += 1
        elif termination in ("Black disconnects", "Black's connection stalls"):
          crash[black] += 1
        else:
          raise ValueError("unknown termination " + termination)
        if not result or result[0] == "*":
          result = simulate(white, black)
        if result:
          lw = result_dict.get(white, [])
          lb = result_dict.get(black, [])
          if result[0] == "1":
            points[white] += 1
            lw.append(("W", black, 1))
          elif result[0] == "1/2":
            points[white] += 0.5
            points[black] += 0.5
            lw.append(("W", black, 0.5))
            lb.append(("B", white, 0.5))
          elif result[0] == "0":
            points[black] += 1
            lb.append(("B", white, 1))
          result_dict[white] = lw
          result_dict[black] = lb
          # print(white, black, result)
    tb_dict = calc_tiebreak(points, crash, result_dict)
    lst = [(points[name], tb_dict[name], name) for name in points]
    lst.sort()
    lst.reverse()
    if False:
      i = 1
      for pts, tb, name in lst:
        cr, sb, black_count, win_count, black_win_count, coin = tb
        print("%2i. %-20s %4.1f %i %6.2f %2i %2i %2i %.2f" % (
          i, name, pts, cr, sb, black_count, win_count, black_win_count, coin))
        i += 1
    if tb_dict[Stockfish] > tb_dict[Komodo]:
      win += 1
    elif tb_dict[Stockfish] == tb_dict[Komodo]:
      draw += 1
    else:
      lost += 1
    for tt in range(len(lst)):
      name = lst[tt][-1]
      pos_dict[name][i + 1] += 1
  print(100.0 * win / simulation_count, 100.0 * draw / simulation_count, 100.0 * lost / simulation_count)
  lst2 = []
  for name in velo:
    c = pos_dict[name]
    if sum(c.values()) == 0:
      continue
    max_value = max(c.values())
    for pos in c:
      if c[pos] == max_value:
        max_pos = pos
        break
    lst2.append((max_pos, -max_value, sum([c[pos] for pos in c if pos <= 8]), name))
  lst2.sort()
  for i in range(len(lst2)):
    max_pos, max_value, above8, name = lst2[i]
    max_value = -max_value
    print("%2i. %-20s" % (i + 1, name), end="")
    if above8:
      print(" %8.4f%%" % (100.0 * above8 / simulation_count,), end="")
    else:
      print(" " * 10, end="")
    for pos in range(1, len(lst2) + 1):
      if pos in pos_dict[name]:
        count = pos_dict[name][pos]
        if count == max_value:
          mark1 = "<"
          mark2 = ">"
        else:
          mark1 = mark2 = " "
        print("  %3s. %6.3f%%%s" % ("%s%i" % (mark1, pos), 100.0 * count / simulation_count, mark2), end="")
      else:
        print(" ", end="")
    print()
