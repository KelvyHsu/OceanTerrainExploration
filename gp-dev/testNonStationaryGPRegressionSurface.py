import numpy as np
import GaussianProcessModel
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import kernels
import responses


def mesh2data(Xmesh, Ymesh, Zmesh = None):

	(xLen, yLen) = Xmesh.shape
	n = xLen * yLen
	data = np.zeros((n, 2))
	data[:, 0] = np.reshape(Xmesh, n)
	data[:, 1] = np.reshape(Ymesh, n)

	if Zmesh == None:
		return(data)
	else:
		z = np.reshape(Zmesh, n)
		return(data, z)

def data2mesh(data, meshshape, zs = None):

	x = data[:, 0]
	y = data[:, 1]

	Xmesh = np.reshape(x, meshshape)
	Ymesh = np.reshape(y, meshshape)

	if zs == None:
		return(Xmesh, Ymesh)
	else:
		
		if type(zs) == int:
			Zmesh = np.reshape(zs, meshshape)
		else:
			Zmesh = zs.copy()
			for i in range(len(zs)):
				Zmesh[i] = np.reshape(zs[i], meshshape)
		return(Xmesh, Ymesh, Zmesh)

# def func(X):

# 	x1 = X[:, 0]
# 	x2 = X[:, 1]
# 	y = (x1 + 5)**2 * np.sin(0.8*(x1 + 5))**2 + 5*x2 + 1
# 	y[x1 > -1] = y[x1 > -1] + 20
# 	y[x1 > 1] = y[x1 > 1] - 20
# 	return(y)

def getBounds(fqExp, fqVar, std = 2, returnStd = False):

	fqStd = np.sqrt(fqVar.diagonal())

	fqU = fqExp + std*fqStd
	fqL = fqExp - std*fqStd

	if returnStd:
		return(fqU, fqL, fqStd)
	else:
		return(fqU, fqL)

def func(X):

	x1 = X[:, 0]
	x2 = X[:, 1]
	y = x1 + x2
	y[x1 + x2 > 0] = y[x1 + x2 > 0] + 10
	return(y)

noiseLevel = 0
numberOfTrainingPoints = 100
numberOfValidationPoints = 800

np.random.seed(300)

halfRange = 5
k = 2
X = 2 * halfRange * (1 - (np.random.rand(numberOfTrainingPoints, k))) - halfRange
x1add = np.linspace(-0.2, 0.4, num = 2)
x2add = np.zeros(x1add.shape)
Xadd = np.concatenate((x1add[:, np.newaxis], x2add[:, np.newaxis]), axis = 1)
X = np.concatenate((X, Xadd), axis = 0)

x1 = X[:, 0]
x2 = X[:, 1]
yTrue = func(X)
y = yTrue+ noiseLevel * np.random.randn(yTrue.shape[0])

xq = np.linspace(-halfRange, halfRange, num = int(np.sqrt(numberOfValidationPoints)))

(xq1Mesh, xq2Mesh) = np.meshgrid(xq, xq)
meshshape = xq1Mesh.shape

Xq = mesh2data(xq1Mesh, xq2Mesh)
yqTrue = func(Xq)

gpr = GaussianProcessModel.NonStationaryGaussianProcessRegression(X, y)
gpr.setInitialHyperLengthScale(15, relative = True)

GaussianProcessModel.VERBOSE = True
np.set_printoptions(precision = 2)
gpr.learn(relearn = 1, optimiseLengthHyperparams = True)
np.set_printoptions(precision = 10)

lengthScales = gpr.predictLengthScales(X)
lengthScalesQ = gpr.predictLengthScales(Xq)

(yqExp, yqVar) = gpr.predict(Xq)
(yqU, yqL, yqStd) = getBounds(yqExp, yqVar, returnStd = True)

(yqExpStat, yqVarStat) = gpr.gpStationary.predict(Xq)
(yqUStat, yqLStat, yqStdStat) = getBounds(yqExpStat, yqVarStat, returnStd = True)

NUMPLTS = 5

(_, _, listOfMeshs) = data2mesh(Xq, meshshape, [yqExp, yqStd, yqExpStat, yqStdStat, yqTrue, lengthScalesQ])

yqExpMesh = listOfMeshs[0]
yqStdMesh = listOfMeshs[1]
yqExpStatMesh = listOfMeshs[2]
yqStdStatMesh = listOfMeshs[3]
yqTrueMesh = listOfMeshs[4]
lengthScalesQMesh = listOfMeshs[5]

minYplt = np.min(np.array([yqTrueMesh.min(), yqExpMesh.min(), yqExpStatMesh.min()])) - 1

fig1 = plt.figure(1)
ax1 = fig1.add_subplot(111, projection = '3d')
ax1.scatter(x1, x2, y, c = 'g', label = 'Raw Data')
ax1.plot_surface(xq1Mesh, xq2Mesh, yqTrueMesh, rstride = 1, cstride = 1, color = 'green', linewidth = 0, antialiased = False, alpha = 0.5, label = 'True Surface')
plt.title('Ground Truth')
ax1.set_xlabel('x1')
ax1.set_ylabel('x2')
ax1.set_zlabel('y')
ax1.legend()

fig2 = plt.figure(2)
ax2 = fig2.add_subplot(111, projection = '3d')
ax2.scatter(x1, x2, y, c = 'g', label = 'Raw Data')
ax2.plot_surface(xq1Mesh, xq2Mesh, yqExpMesh, rstride = 1, cstride = 1, cmap = cm.coolwarm, linewidth = 0, antialiased = False, label = 'GP Predicted Surface')
ax2.plot_surface(xq1Mesh, xq2Mesh, yqTrueMesh, color = 'green', alpha = 0.1, label = 'True Surface')
levels = np.linspace(np.min(yqStdMesh),np.max(yqStdMesh), 50)
contourPlt = ax2.contour(xq1Mesh, xq2Mesh, yqStdMesh, levels, zdir = 'z', offset = minYplt, cmap = cm.coolwarm)
fig2.colorbar(contourPlt, shrink = 0.5, aspect = 5)
plt.title('Non-Stationary Gaussian Process Prediction')
ax2.set_xlabel('x1')
ax2.set_ylabel('x2')
ax2.set_zlabel('y')
ax2.legend()

fig3 = plt.figure(3)
ax3 = fig3.add_subplot(111, projection = '3d')
ax3.scatter(x1, x2, y, c = 'g', label = 'Raw Data')
ax3.plot_surface(xq1Mesh, xq2Mesh, yqExpStatMesh, rstride = 1, cstride = 1, cmap = cm.coolwarm, linewidth = 0, antialiased = False, label = 'GP Predicted Surface')
ax3.plot_surface(xq1Mesh, xq2Mesh, yqTrueMesh, color = 'green', alpha = 0.1, label = 'True Surface')
levels = np.linspace(np.min(yqStdStatMesh),np.max(yqStdStatMesh), 50)
contourPlt = ax3.contour(xq1Mesh, xq2Mesh, yqStdStatMesh, levels, zdir = 'z', offset = minYplt, cmap = cm.coolwarm)
fig3.colorbar(contourPlt, shrink = 0.5, aspect = 5)
plt.title('Stationary Gaussian Process Prediction')
ax3.set_xlabel('x1')
ax3.set_ylabel('x2')
ax3.set_zlabel('y')
ax3.legend()

fig4 = plt.figure(4)
ax4 = fig4.add_subplot(111, projection = '3d')
ax4.plot_surface(xq1Mesh, xq2Mesh, lengthScalesQMesh, rstride = 1, cstride = 1, cmap = cm.coolwarm, linewidth = 0, antialiased = False, label = 'GP Underlying Length Scale')
ax4.plot_surface(xq1Mesh, xq2Mesh, gpr.getStationaryLengthScale() * np.ones(lengthScalesQMesh.shape), color = 'green', alpha = 0.1, label = 'Stationary GP Underlying Length Scale')
plt.title('Underlying Length Scale')
ax4.set_xlabel('x1')
ax4.set_ylabel('x2')
ax4.set_zlabel('y')

lineStripIndices = (-0.5 < x2) & (x2 < 0.5)
x1_1D = x1[lineStripIndices]
x2_1D = x2[lineStripIndices]
y_1D = y[lineStripIndices]
X_1D = np.concatenate((x1_1D[:, np.newaxis], x2_1D[:, np.newaxis]), axis = 1) 

x1q_1D = np.linspace(-halfRange, halfRange, num = 200)
x2q_1D = np.zeros(x1q_1D.shape)
Xq_1D = np.concatenate((x1q_1D[:, np.newaxis], x2q_1D[:, np.newaxis]), axis = 1)

yqTrue_1D = func(Xq_1D)

(yqExp_1D, yqVar_1D) = gpr.predict(Xq_1D)
(yqU_1D, yqL_1D, yqStd_1D) = getBounds(yqExp_1D, yqVar_1D, returnStd = True)

(yqExpStat_1D, yqVarStat_1D) = gpr.gpStationary.predict(Xq_1D)
(yqUStat_1D, yqLStat_1D, yqStdStat_1D) = getBounds(yqExpStat_1D, yqVarStat_1D, returnStd = True)

lengthScales_1D = gpr.predictLengthScales(X_1D)
lengthScalesQ_1D = gpr.predictLengthScales(Xq_1D)

plt.figure(5)
plt.subplot(3, 1, 1)
plt.scatter(x1_1D, y_1D, c = x2_1D, cmap = cm.coolwarm, label = 'Raw Data')
plt.plot(x1q_1D, yqTrue_1D, c = 'g', label = 'Actual Function')
plt.plot(x1q_1D, yqExp_1D, c = 'b', label = 'GP Predicted Function')
plt.fill_between(x1q_1D, yqU_1D, yqL_1D, facecolor = 'cyan', alpha = 0.2)
plt.title('Non-Stationary Gaussian Process Result (slice at x2 = 0)')
plt.xlabel('x1')
plt.ylabel('y')
plt.legend(loc = 'upper left')
cbar = plt.colorbar()
cbar.set_label('x2')

plt.subplot(3, 1, 2)
plt.scatter(x1_1D, y_1D, c = x2_1D, cmap = cm.coolwarm, label = 'Raw Data')
plt.plot(x1q_1D, yqTrue_1D, c = 'g', label = 'Actual Function')
plt.plot(x1q_1D, yqExpStat_1D, c = 'b', label = 'GP Predicted Function')
plt.fill_between(x1q_1D, yqUStat_1D, yqLStat_1D, facecolor = 'cyan', alpha = 0.2)
plt.title('Stationary Gaussian Process Result (slice at x2 = 0)')
plt.xlabel('x1')
plt.ylabel('y')
plt.legend(loc = 'upper left')
cbar = plt.colorbar()
cbar.set_label('x2')

plt.subplot(3, 1, 3)
plt.scatter(x1_1D, lengthScales_1D, c = x2_1D, cmap = cm.coolwarm)
plt.plot(x1q_1D, lengthScalesQ_1D)
plt.plot(x1q_1D, gpr.stationaryLengthScale * np.ones(x1q_1D.shape), c = 'g')
plt.title('Underlying Length Scale (slice at x2 = 0)')
plt.xlabel('x1')
plt.ylabel('Length Scale')
cbar = plt.colorbar()
cbar.set_label('x2')

print('Stationary & Non-Stationary GP Kernel Sensitivity:', gpr.getSensitivity())
print('Stationary GP Length Scale:', gpr.getStationaryLengthScale())
print('Stationary & Non-Stationary GP Noise Level:', gpr.getNoiseLevel())
print('Length Scale GP Kernel Hyperparameters:', gpr.getLengthScaleKernelHyperparams())
print('Length Scale GP Noise Level:', gpr.getLengthScaleNoiseLevel())
print('Initial Hyper Length Scale Factor:', gpr.getInitialHyperLengthScale())
print('Minimum Hyper Length Scale Factor:', gpr.getMinHyperLengthScale())
print('Hyper Length Scale Factor:', gpr.getCurrentHyperLengthScale())
print('Initial Hyper Length Scale Factor (Relative):', gpr.getInitialHyperLengthScale(relative = True))
print('Minimum Hyper Length Scale Factor (Relative):', gpr.getMinHyperLengthScale(relative = True))
print('Hyper Length Scale Factor (Relative):', gpr.getCurrentHyperLengthScale(relative = True))

plt.show()
