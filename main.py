#!/usr/bin/env python3
import re

def normalize_string(s):
  return re.sub("\s+", " ", s.strip().title())
assert("Word345_ Other" == normalize_string(" wOrd345_  other"))

def dict_combine(a, b, combiner):
  """ Return union of dicts a and b. Values of common keys are passed to
      combiner and the results become the values """
  def create_or_combine(d, key, value):
    if key in d:
      d[key] = combiner(d[key], value)
    else:
      d[key] = value
  d = {}
  d.update(a)
  for key, value in b.items():
    create_or_combine(d, key, value)
  return d

def dict_addition(a, b):
  """ Return union of dicts a and b. Values of common keys are added """
  return dict_combine(a, b, lambda x, y: x + y)
assert(dict_addition({'a':2, 'b':1}, {'b':10, 'c':5}) == {'a':2, 'b':11, 'c':5})

class UnitParsingError(RuntimeError):
  pass

class Unit(object):
  """
    A unit that can have an arbitrary number of dimensions, each to an integer power
    Example: m/s, Pa*m^2, cakes/fortnight
  """
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
      (r"\((.+)\)\^([\-0-9]+)", lambda m: Unit.parse(m.group(1)).power_of(int(m.group(2)))),
      # u ^ int
      (r"([^/*]+)\^([\-0-9]+)", lambda m: Unit.parse(m.group(1)).power_of(int(m.group(2)))),
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
        unit = action(match)
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
    raise UnitParsingError("'%s' cannot be parsed as a Unit" %(string,))

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

  def __hash__(self):
    return hash(str(self))

  def __repr__(self):
    return "<Unit %s>" %(''.join(["%s^%d" %(name, exp) for name, exp in self.dims.items()]),)

assert(Unit() == Unit())
assert(Unit.parse('m^-1') == Unit.parse('1/m'))
assert(Unit.parse('m/(s^2)') == Unit.parse('m/s/s'))
assert(Unit.parse('(m/s)/s') != Unit.parse('m/(s/s)'))
assert(Unit.parse('m') == Unit.parse('m/(s/s)'))
assert(Unit.parse('Pa*m^3').dims == {'Pa': 1, 'm': 3})
assert(Unit.parse('m^3*Pa').dims == {'Pa': 1, 'm': 3})
assert(Unit.parse('(Pa*m)^3').dims == {'Pa': 3, 'm': 3})
assert(Unit.parse('(Pa*(m))^3').dims == {'Pa': 3, 'm': 3})
assert(Unit.parse('(Pa*(m)^3)').dims == {'Pa': 1, 'm': 3})

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

  def __repr__(self):
    return "<Measurement: %s %s>" %(self.value, self.unit)

assert(Measurement.parse('2 m') != Measurement.parse('3 m'))
assert(Measurement.parse('2 m').multiply(Measurement.parse('3 s'))
       == Measurement.parse('6 m*s'))

class Problem(object):
  def __init__(self):
    self.measurements = {}
    self.add(Measurement(1, Unit()))

  def add(self, measurement):
    assert(measurement.unit not in self.measurements)
    new_derived = [m.multiply(measurement) for m in self.measurements.values()] + \
                  [m.multiply(measurement.invert()) for m in self.measurements.values()]
    for m in new_derived:
      if m.unit not in self.measurements:
        self.measurements[m.unit] = m
    self.measurements[measurement.unit] = measurement

  def query(self, unit):
    """ Try to determine the value with the given unit using dimensional analysis on
         the known Measurements. Returns None if it cannot be determined """
    assert(isinstance(unit, Unit))
    if unit in self.measurements:
      return self.measurements[unit]
    print("%s cannot determine value in unit '%s'" %(self, unit))
    return None

  def __repr__(self):
    #return "<Problem: %s>" %('\n  '.join([str(m) for m in self.measurements.values()]),)
    return "<Problem: %s>" %(self.measurements,)

def main():
  import sys
  p = Problem()
  for line in sys.stdin:
    try:
      p.add(Measurement.parse(line))
    except MeasurementParsingError:
      measurement = p.query(Unit.parse(line))
      if measurement is not None:
        print(measurement.value)


def test():
  import math
  def assertMeasurement(a, b, *args, **kwargs):
    assert(a.unit == b.unit)
    assert(math.isclose(a.value, b.value, *args, **kwargs))

  # Simple s = vt, querying t
  p = Problem()
  p.add(Measurement.parse('3 m/s'))
  p.add(Measurement.parse('2 m'))
  assert(Unit.parse('s') in p.measurements)
  assert(p.query(Unit.parse('s')))
  assertMeasurement(p.query(Unit.parse('s')), Measurement.parse("0.666666 s"), rel_tol=1e-5)


  # Temperature from Universal Gas Law
  P, V, n, R = [Measurement.parse('1001 Pa'),
                Measurement.parse('2.3 m^3'),
                Measurement.parse('304 mol'),
                Measurement.parse('8.3145 Pa*m^3/(mol*K)')]
  p = Problem()
  p.add(P)
  p.add(V)
  p.add(n)
  p.add(R)
  # Solving for the expected T in the Universal Gas Law PV = nRT
  T = Measurement(P.value * V.value / (n.value * R.value), Unit.parse('K'))
  assertMeasurement(p.query(Unit.parse('K')), T, rel_tol=1e-5)

test()
if __name__ == '__main__':
  main()
