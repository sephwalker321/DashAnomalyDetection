"""============================================================================
Python implementation of Bayesian online changepoint detection for a normal
model with unknown mean parameter. For details, see Adams & MacKay 2007:
    "Bayesian Online Changepoint Detection"
    https://arxiv.org/abs/0710.3742

Contents:
- BOCPD

Author: Joseph Walker j.j.walker@durham.ac.uk
============================================================================"""
import numpy as np
from sklearn.preprocessing import StandardScaler
#tol: Truncate the matrix R when P < tol
BOCPD_tol = 1e-2
#MaxSeqLength: Truncate the matrix sequence length dimension
BOCPD_MaxSeqLength = 100
#hazard: The estimated CP rate. 
BOCPD_hazard = 1/100

################################################################################################################
# Functions:
################################################################################################################

######################
# BOCPD:
######################

def bocd(data, errs):
	"""The BOCPD algorithum, Return run length posterior using Algorithm 1 in Adams & MacKay 2007.
	data: Timeseries data
	errs: The assoicated errs on the data (or scaled)
	Return,
	R: The BOCP probability matrix
	"""
	#scaler = StandardScaler()
	#scaler.fit(data.reshape(-1, 1))
	#data = scaler.transform(data.reshape(-1, 1))[:,0]
	#errs = scaler.transform(errs.reshape(-1, 1))[:,0]

	# 1. Initialize lower triangular matrix representing the posterior as
	# function of time. Model parameters are initialized in the model class.
	T = data.shape[0]
	R = np.zeros((T, T + 1), dtype=np.float64)
	R[:, 0] = 1.0
	message = R[0,:0+1]

	pdf = lambda x, mu, sig: np.exp(-0.5*((x-mu)/sig)**2.0)/(sig*np.sqrt(2*np.pi))
	pdflog = lambda x, mu, sig: -0.5*((x-mu)/sig)**2.0 - np.log(sig*np.sqrt(2*np.pi))

	MaxMessage = 1
	for t in range(1, T):
		# 2. Evaluate predictive probabilities.

		M = len(message)
		pis = np.zeros(M)
		#pislog = np.zeros(M)
		mean_params = np.zeros(M)
		sig_params = np.zeros(M)
		for i in range(0,M):
			dat_i = data[t-i-1:t+1]
			errs_i = errs[t-i-1:t+1]

			mean_params[i] = np.nanmean(dat_i)
			sig_params[i] = np.nanmax(errs_i)+BOCPD_tol
			pis[i] = pdf(data[t], mean_params[i], sig_params[i])
			#print(pis[i],mean_params[i], sig_params[i])
			#pislog[i] = pdflog(data[t], mean_params[i], sig_params[i])

		# 4. Calculate growth probabilities.
		growth_probs = pis * message * (1 - BOCPD_hazard)

 
		# 5. Calculate changepoint probabilities.
		cp_prob = sum(message*BOCPD_hazard)

     
		# 6. Calculate evidence
		new_joint = np.append(cp_prob, growth_probs)
       
		# 7. Determine run length distribution.
		new_joint /= sum(new_joint)

		# Setup message passing.
		psum = np.cumsum(new_joint[::-1])
		Array = psum[::-1]<BOCPD_tol

		if Array.any() == True:
			seqlen = -1
			for i in range(len(new_joint)):
				if Array[i] == True:
					seqlen = i
					break
			new_joint = new_joint[:seqlen]

		R[t, :len(new_joint)] = new_joint
		message = new_joint

		if len(message)-1 > MaxMessage:
			MaxMessage = len(message)-1


	R_Max = np.argmax(R,axis=1)
	Ps = [ R[i,R_Max[i]] for i in range(R.shape[0])]
	if R.shape[0] > 1:
		if MaxMessage > BOCPD_MaxSeqLength:
			MaxMessage = BOCPD_MaxSeqLength
		if MaxMessage < R.shape[1]:
			R = R[:,:int(MaxMessage)] #Truncate
	return R, R_Max, Ps

if __name__ == "__main__":
	print("Run as module") 
