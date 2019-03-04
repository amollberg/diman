#!/usr/bin/env python3
import re

def normalize_string(s):
  return re.sub("\s+", " ", s.strip().title())
assert("Word345_ Other" == normalize_string(" wOrd345_  other"))

def dict_addition(a, b):
  """ Return union of dicts a and b. Values of common keys are added """
  def create_or_add(d, key, value):
    if key in d:
      d[key] += value
    else:
      d[key] = value
  d = {}
  d.update(a)
  for key, value in b.items():
    create_or_add(d, key, value)
  return d
assert(dict_addition({'a':2, 'b':1}, {'b':10, 'c':5})=={'a':2, 'b':11, 'c':5})

class UnitParsingError(RuntimeError):
  pass

class Unit(object):
  def __init__(self):
    self.dims = {}

  @staticmethod
  def _create(dims):
    unit = Unit()
    unit.dims = dims
    unit.normalize()
    return unit

  @staticmethod
  def parse(string):
    """ Parse a string as representation of a Unit """
    def trivial_unit(dimension_name):
      unit = Unit()
      if dimension_name != '1':
        unit.dims[dimension_name] = 1
      return unit
    cases = [
      # (u)
      (r"\((.+)\)", lambda m: Unit.parse(m.group(1))),
      # u ^ int
      (r"U\^([\-0-9]+)", lambda m: Unit.parse(m.group(1)).power_of(int(m.group(2)))),
      # u / u
      (r"U/U",
       lambda m: Unit.parse(m.group(1)).multiply(Unit.parse(m.group(2)).invert())),
      # u * u
      (r"U\*U",
       lambda m: Unit.parse(m.group(1)).multiply(Unit.parse(m.group(2)))),
      # terminal
      (r"(\w+)", lambda m: trivial_unit(m.group(1))),]
    def try_pattern(pattern, action):
      match = re.match("^" + pattern + "$", string)
      if match:
        print("=> %s matches %s"%(string, pattern))
        unit = action(match)
        print("<= %s returns %s" %(string, unit.dims))
        return unit
      return None
    variants = ["\((.+)\)", "(.+)"]
    for pattern, action in cases:
      for first_replacement in variants:
        half_pattern = pattern.replace("U", first_replacement, 1)
        for second_replacement in variants:
          full_pattern = half_pattern.replace("U", second_replacement, 1)
          unit = try_pattern(full_pattern, action)
          if unit is not None:
            return unit
    raise UnitParsingError("'%s' cannot be parsed as a Unit"%(string,))

  def invert(self):
    return Unit._create({name : -exp for name, exp in self.dims.items()})

  def multiply(self, other_unit):
    return Unit._create(dict_addition(self.dims, other_unit.dims))

  def power_of(self, n):
    return Unit._create({name : exp * n for name, exp in self.dims.items()})

  def normalize(self):
    self.dims = {name : value for name, value in self.dims.items()
                 if value != 0}

  def __eq__(self, other):
    return self.dims == other.dims

assert(Unit() == Unit())
assert(Unit.parse('m^-1') == Unit.parse('1/m'))
assert(Unit.parse('m/(s^2)') == Unit.parse('m/s/s'))
assert(Unit.parse('(m/s)/s') != Unit.parse('m/(s/s)'))
assert(Unit.parse('m') == Unit.parse('m/(s/s)'))

class MeasurementParsingError(RuntimeError):
  pass

class Measurement(object):
  def __init__(self, value, unit):
    self.value = value
    self.unit = unit

  @staticmethod
  def parse(string):
    match = re.match(r"^(?P<value>(\S+)) (?P<unit>(.+))$", string)
    if match:
      return Measurement(float(match.group('value')), Unit.parse(match.group('unit')))
    raise MeasurementParsingError("'%s' cannot be parsed as a Measurement" %(string,))

  def multiply(self, other):
    return Measurement(self.value * other.value,
                       self.unit.multiply(other.unit))

  def invert(self):
    return Measurement(1.0/self.value, self.unit.invert())

  def power_of(self, n):
    return Measurement(self.value**n, self.unit.power_of(n))

  def __eq__(self, other):
    return self.value == other.value and self.unit == other.unit

assert(Measurement.parse('2 m') != Measurement.parse('3 m'))
assert(Measurement.parse('2 m').multiply(Measurement.parse('3 s'))
       == Measurement.parse('6 m*s'))

class Problem(object):
  def __init__(self):
    self.measurements = {}

  def add(self, measurement):
    assert(measurement.unit not in self.measurements.keys())
    for m in self.measurements:
      pass # TODO

    self.measurements[measurement.unit] = measurement

  def query(self, unit):
    if unit in self.measurements.keys():
      return unit


def main():
  pass

def test():
  # enter 2 m, 3 m/s, s => get 0.666
  pass

test()
if __name__ == '__main__':
  main()
