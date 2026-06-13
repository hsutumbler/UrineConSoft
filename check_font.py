import sys
import matplotlib.pyplot as plt
from matplotlib.font_manager import findfont, FontProperties

prop = FontProperties(family=['PingFang HK', 'sans-serif'])
print("Picked font file:", findfont(prop))
