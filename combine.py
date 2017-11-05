#!/usr/bin/env python3
import re

pat = r".*?(Rank.*)ResultSet-.*(Rank.*)ResultSet-"


def read_ratings(filename):
  s = open(filename).read()
  m = re.match(pat, s, re.DOTALL)
  return m.group(2), m.group(1)


def convert2table(s):
  line_lst = s.split("\n")
  total_len = len(line_lst[0])
  SPACE = 0
  VALUE = 1
  state = VALUE
  splits = [0]
  for i in range(total_len):
    for line in line_lst:
      if not line:
        continue
      if line[i] != " ":
        if state == SPACE:
          state = VALUE
        break
    else:
      if state == VALUE:
        state = SPACE
        splits.append(i)
  table = []
  values_dict = {}
  for line in line_lst:
    if not line:
      continue
    lst = []
    for i in range(len(splits) - 1):
      lst.append(line[splits[i]:splits[i + 1]])
    table.append(lst)
    values_dict[lst[1].strip()] = lst
  return table, values_dict


def parse_int(s):
  m = re.match(r".*?(\d+)", s)
  if m:
    return int(m.group(1))
  return 0


def diff_ratings(old, new, as_string=True):
  old_table, old_values = convert2table(old)
  new_table, new_values = convert2table(new)
  result = []
  max_width = [0] * len(new_table[0])
  for result_flag in (False, True):
    for i in range(len(new_table)):
      name = new_table[i][1].strip()
      if name in old_values:
        for j in (0, 2, 5):
          old_v = parse_int(old_values[name][j])
          new_v = parse_int(new_values[name][j])
          if result_flag:
            s = ""
            if old_v != new_v:
              diff = new_v - old_v
              if j == 0:
                diff = -diff
              if diff > 0:
                s = "(+%i)" % diff
              else:
                s = "(%i)" % diff
            s += " " * (max_width[j] - len(s))
            new_values[name][j] += s
          else:
            if old_v != new_v:
              max_width[j] = max(max_width[j], 3 + len(str(int(new_v - old_v))))
      if result_flag:
        if as_string:
          result.append("".join(new_values[name]))
        else:
          result.append(new_values[name])
  if as_string:
    return "\n".join(result)
  else:
    return result


if __name__ == "__main__":
  with open("ratings_combined.txt", "w") as fp:
    for header, filename in (("""One name used for each program in season
One name used for each program in season despite updates unless it has played in previous season.
Rybka 4.1 is used as offset at 3100.
Difference for some values in parenthesis if any.
Created using https://www.remi-coulom.fr/Bayesian-Elo/ and some local scripts.
Search for 'version' for individual rating for each version.
Search for 'One rating' for one rating for each progam (not useful).

""", "ratings.txt"),
                             ("Individual ratings for each version\n\n", "ratings.txt"),
                             ("One rating for each program\nNot useful, too much strength increase\n\n",
                              "ratingsP.txt")):
      fp.write(header)
      old_now, old_full = read_ratings("t/" + filename)
      now, full = read_ratings(filename)
      now = diff_ratings(old_now, now)
      full = diff_ratings(old_full, full)
      fp.write(now)
      fp.write("\n\n")
      fp.write(full)
      fp.write("\n\n")
