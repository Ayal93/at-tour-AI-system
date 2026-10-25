import numpy as np                      # arrays and math
import pandas as pd                     # load CSV / Excel data
import matplotlib.pyplot as plt         # plot loss and results

import torch                            # tensors and training
import torch.nn as nn                   # layers and loss functions
import torch.optim as optim             # optimizers (Adam, SGD)
from torch.utils.data import DataLoader, TensorDataset   # batching

from sklearn.model_selection import train_test_split     # split data
from sklearn.preprocessing import StandardScaler         # scale inputs
from sklearn.metrics import mean_squared_error, accuracy_score


