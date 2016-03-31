"""
==========================================
LocalOutlierFactor benchmark
==========================================

A test of LocalOutlierFactor on classical anomaly detection datasets.

"""
print(__doc__)

from time import time
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import LocalOutlierFactor
from sklearn.metrics import roc_curve, auc
from sklearn.datasets import fetch_kddcup99, fetch_covtype, fetch_mldata
from sklearn.datasets import fetch_spambase, fetch_annthyroid, fetch_arrhythmia
from sklearn.preprocessing import LabelBinarizer
from sklearn.utils import shuffle as sh
from scipy.interpolate import interp1d

np.random.seed(1)

nb_exp = 2

# datasets available: ['http', 'smtp', 'SA', 'SF', 'shuttle', 'forestcover']
datasets = ['arrhythmia']  # ['http', 'smtp', 'shuttle', 'forestcover', 'ionosphere', 'spambase', 'annthyroid']

for dat in datasets:
    # loading and vectorization
    print('loading data')

    if dat == 'arrhythmia':
        dataset = fetch_arrhythmia(shuffle=True)
        X = dataset.data
        y = dataset.target
        # rm 5 features containing some '?' (XXX to be mentionned in paper)
        X = np.delete(X, [10, 11, 12, 13, 14], axis=1)
        y = (y != 1).astype(int)
        # normal data are then those of class 1

    if dat == 'annthyroid':
        dataset = fetch_annthyroid(shuffle=True)
        X = dataset.data
        y = dataset.target
        y = (y != 3).astype(int)
        # normal data are then those of class 3

    if dat == 'spambase':
        dataset = fetch_spambase(shuffle=True)
        X = dataset.data
        y = dataset.target

    if dat == 'ionosphere':
        dataset = fetch_mldata('ionosphere')
        X = dataset.data
        y = dataset.target
        X, y = sh(X, y)
        y = (y != 1).astype(int)

    if dat in ['http', 'smtp', 'SA', 'SF']:
        dataset = fetch_kddcup99(subset=dat, shuffle=True, percent10=False)
        X = dataset.data
        y = dataset.target

    if dat == 'shuttle':
        dataset = fetch_mldata('shuttle')
        X = dataset.data
        y = dataset.target
        sh(X, y)
        # we remove data with label 4
        # normal data are then those of class 1
        s = (y != 4)
        X = X[s, :]
        y = y[s]
        y = (y != 1).astype(int)

    if dat == 'forestcover':
        dataset = fetch_covtype(shuffle=True)
        X = dataset.data
        y = dataset.target
        # normal data are those with attribute 2
        # abnormal those with attribute 4
        s = (y == 2) + (y == 4)
        X = X[s, :]
        y = y[s]
        y = (y != 2).astype(int)

    print('vectorizing data')

    if dat == 'SF':
        lb = LabelBinarizer()
        lb.fit(X[:, 1])
        x1 = lb.transform(X[:, 1])
        X = np.c_[X[:, :1], x1, X[:, 2:]]
        y = (y != 'normal.').astype(int)

    if dat == 'SA':
        lb = LabelBinarizer()
        lb.fit(X[:, 1])
        x1 = lb.transform(X[:, 1])
        lb.fit(X[:, 2])
        x2 = lb.transform(X[:, 2])
        lb.fit(X[:, 3])
        x3 = lb.transform(X[:, 3])
        X = np.c_[X[:, :1], x1, x2, x3, X[:, 4:]]
        y = (y != 'normal.').astype(int)

    if dat == 'http' or dat == 'smtp':
        y = (y != 'normal.').astype(int)

    n_samples, n_features = np.shape(X)
    n_samples_train = n_samples // 2
    n_samples_test = n_samples - n_samples_train
    X = X.astype(float)

    n_axis = 1000
    x_axis = np.linspace(0, 1, n_axis)
    tpr = np.zeros(n_axis)
    fit_time = 0
    predict_time = 0

    for ne in range(nb_exp):
        print 'exp num:', ne
        indices = np.arange(X.shape[0])
        np.random.shuffle(indices)  # shuffle the dataset
        X = X[indices]
        y = y[indices]

        X_train = X[:n_samples_train, :]
        X_test = X[n_samples_train:, :]
        y_train = y[:n_samples_train]
        y_test = y[n_samples_train:]

        # training only on normal data:
        X_train = X_train[y_train == 0]
        y_train = y_train[y_train == 0]

        print('LocalOutlierFactor processing...')
        model = LocalOutlierFactor(n_neighbors=20)
        tstart = time()
        model.fit(X_train)
        fit_time += time() - tstart
        tstart = time()

        scoring = -model.decision_function(X_test)  # the lower,the more normal
        predict_time += time() - tstart
        fpr_, tpr_, thresholds_ = roc_curve(y_test, scoring)

        f = interp1d(fpr_, tpr_)
        tpr += f(x_axis)
        tpr[0] = 0.

    tpr /= float(nb_exp)
    fit_time /= float(nb_exp)
    predict_time /= float(nb_exp)
    AUC = auc(x_axis, tpr)
    plt.plot(x_axis, tpr, lw=1, label='ROC for %s (area = %0.3f, train-time: %0.2fs, test-time: %0.2fs)' % (dat, AUC, fit_time, predict_time))

plt.xlim([-0.05, 1.05])
plt.ylim([-0.05, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic for LocalOutlierFactor')
plt.legend(loc="lower right")
plt.show()