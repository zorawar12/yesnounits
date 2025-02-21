# Author: Swadhin Agrawal
# E-mail: swadhin12a@gmail.com

from random import uniform
import numpy as np
# from multiprocessing import Pool
from multiprocessing.pool import ThreadPool as Pool
import matplotlib.pyplot as plt
import itertools
import pandas as pd
import Object as obj
import DecisionMaking as DM
import Params as params
import ParamSet as ps
import os
from functools import partial
import copy
from scipy.special import lambertw

def parallel(func,inputs):
	batch_size = len(inputs)
	inps = [(i,) for i in inputs]
	output = []
	for i in range(0,len(inputs),batch_size):
		opt_var = []
		with Pool(20) as processor:#,ray_address="auto") as p:
			opt_var = processor.starmap(func,inps[i:i+batch_size])

		output += list(opt_var)
	return output

def option_assignment(num_opts,num_robo):
    opts = np.arange(1,num_opts+1)
    assig = np.copy(opts)
    for i in range(int(num_robo/num_opts)):
        assig = np.concatenate((assig,np.copy(opts)))
    np.random.shuffle(assig)
    return assig

def deciding_phase(p,robots,time_counter):
    options = []
    for o in range(p.num_opts):
        options.append(obj.Object(id = o, o_type = 'O', p = p))
    opt_assignment =  option_assignment(num_opts = p.num_opts, num_robo = p.num_opts*p.mu_m_1)
    for r in robots:
        r.response = 0
        r.assigned_opt = opt_assignment[r.id]

    decision = DM.DecisionMaking(robots,options,p,time_counter,p.memory_length,p.threshold_step)

    matching = decision.compare_with_best(options)
    
    return decision, options

def looper(p,vP):
    opt_assignment = option_assignment(num_opts = p.num_opts, num_robo = p.num_opts*p.mu_m_1)
    robots = []
    for r in range(p.num_robots):
        robots.append(obj.Object(id = r, o_type = 'R', p = p, option = opt_assignment[r]))
    options = []
    for o in range(p.num_opts):
        options.append(obj.Object(id = o, o_type = 'O', p = p))

    for run in range(1000):
        if run%100 == 0:
            opt_assignment =  option_assignment(num_opts = p.num_opts, num_robo = p.num_opts*p.mu_m_1)
            robots = []
            for r in range(p.num_robots):
                robots.append(obj.Object(id = r, o_type = 'R', p = p, option = opt_assignment[r]))
            options = []
            for o in range(p.num_opts):
                options.append(obj.Object(id = o, o_type = 'O', p = p))

            for t in range(1000):
                decision,options = deciding_phase(p,robots,t)
                if decision.threshold_update:
                    decision.updateThresholds(robots,p,vP)

        else:
            decision,options = deciding_phase(p,robots,1)
            if decision.threshold_update:
                decision.updateThresholds(robots,p,vP)
         
        data = {'$\mu_{h_1}$':p.mu_h_1,'$\sigma_{h_1}$':p.sigma_h_1,'$x_{max}$ opt No.':decision.ref_best,'$x_{max}$':options[decision.ref_best].quality,'$CDM$ opt No.':decision.best_option,'$CDM$':options[decision.best_option].quality}
        for i in range(len(robots)):
            data[str(i)] = robots[i].threshold
            data['Response_'+str(i)] = robots[i].response
        data['mem_size'] = p.memory_length
        data['thr_step'] = p.threshold_step

        out = pd.DataFrame(data=[data],columns=p.data_columns_name)
        out.to_csv(p.data_f_path,mode = 'a',header = False, index=False)
        

def paramObjects(fixed_params,vP_,data_columns,path,fixed_params_column):
    p = params.Params(data_columns,path)
    p.initializer(vP_,n = fixed_params[0]['n'], Dm = fixed_params[0]['$D_{m}$'], mum1 = fixed_params[0]['$\mu_{m_{1}}$'],\
        mum2 = fixed_params[0]['$\mu_{m_{2}}$'], sm1 = fixed_params[0]['$\sigma_{m_{1}}$'], sm2 = fixed_params[0]['$\sigma_{m_{2}}$'],\
        dmum = vP_.delta_mu_m, Dx = fixed_params[0]['$D_{x}$'], mux1 = fixed_params[0]['$\mu_{x_{1}}$'],\
        mux2 = fixed_params[0]['$\mu_{x_{2}}$'], sx1 = fixed_params[0]['$\sigma_{x_{1}}$'], sx2 = fixed_params[0]['$\sigma_{x_{2}}$'],\
        dmux = vP_.delta_mu_x, Dh = fixed_params[0]['$D_{h}$'], muh1 = fixed_params[0]['$\mu_{h_{1}}$'],\
        muh2 = fixed_params[0]['$\mu_{h_{2}}$'], sh1 = fixed_params[0]['$\sigma_{h_{1}}$'], sh2 = fixed_params[0]['$\sigma_{h_{2}}$'],\
        dmuh = fixed_params[0]['$\delta_{\mu_{h}}$'], beta = fixed_params[0]['beta'])

    p.packaging(vP_)
    p.add_columns(p.num_robots)
    p.pre = p.prefix(path)
    p.save_params(fixed_params_column,fixed_params,path)
    p.save_data(path)
    return p

if __name__=="__main__":
    path = os.getcwd() + "/results/"

    data_columns = ['$\mu_{h_1}$','$\sigma_{h_1}$','$x_{max}$ opt No.','$x_{max}$','$CDM$ opt No.','$CDM$']
    
    packed_parameters = []
    vP = ps.variableParams()
    betaM = 0
    gumbelM = 1
    uniformM = 0
    if betaM:
        for beta in vP.betas:
            for n in vP.num_opts[:5]:
                fixed_params_column = ['n','$D_{m}$','$\mu_{m_{1}}$','$\mu_{m_{2}}$','$\sigma_{m_{1}}$','$\sigma_{m_{2}}$',\
                    '$D_{x}$','$\mu_{x_{1}}$','$\mu_{x_{2}}$','$\sigma_{x_{1}}$','$\sigma_{x_{2}}$',\
                    '$D_{h}$','$\mu_{h_{1}}$','$\mu_{h_{2}}$','$\sigma_{h_{1}}$','$\sigma_{h_{2}}$','$\delta_{\mu_{h}}$','beta'] 
                fixed_params = [{'n': n, '$D_{m}$':vP.Dm[0],'$\mu_{m_{1}}$':vP.mu_m_1[1],'$\mu_{m_{2}}$':vP.mu_m_2[1],\
                    '$\sigma_{m_{1}}$':vP.sigma_m_1[0],'$\sigma_{m_{2}}$':vP.sigma_m_2[0],'$D_{x}$':vP.Dx[0],\
                    '$\mu_{x_{1}}$':vP.mu_x_1[99],'$\mu_{x_{2}}$':vP.mu_x_2[99],'$\sigma_{x_{1}}$':vP.sigma_x_1[9],\
                    '$\sigma_{x_{2}}$':vP.sigma_x_2[9], '$D_{h}$':None, '$\mu_{h_{1}}$': 13, '$\mu_{h_{2}}$': 13,\
                    '$\sigma_{h_{1}}$':0, '$\sigma_{h_{2}}$':0,'$\delta_{\mu_{h}}$':0,'beta': beta}]

                packed_parameters.append(paramObjects(fixed_params=fixed_params,vP_=vP,data_columns=copy.copy(data_columns),path=path,fixed_params_column=fixed_params_column))
    elif gumbelM:
        for n in vP.num_opts[:5]:
            fixed_params_column = ['n','$D_{m}$','$\mu_{m_{1}}$','$\mu_{m_{2}}$','$\sigma_{m_{1}}$','$\sigma_{m_{2}}$',\
                '$D_{x}$','$\mu_{x_{1}}$','$\mu_{x_{2}}$','$\sigma_{x_{1}}$','$\sigma_{x_{2}}$',\
                '$D_{h}$','$\mu_{h_{1}}$','$\mu_{h_{2}}$','$\sigma_{h_{1}}$','$\sigma_{h_{2}}$','$\delta_{\mu_{h}}$','beta'] 
            fixed_params = [{'n': n, '$D_{m}$':vP.Dm[0],'$\mu_{m_{1}}$':vP.mu_m_1[1],'$\mu_{m_{2}}$':vP.mu_m_2[1],\
                '$\sigma_{m_{1}}$':vP.sigma_m_1[0],'$\sigma_{m_{2}}$':vP.sigma_m_2[0],'$D_{x}$':vP.Dx[0],\
                '$\mu_{x_{1}}$':vP.mu_x_1[99],'$\mu_{x_{2}}$':vP.mu_x_2[99],'$\sigma_{x_{1}}$':vP.sigma_x_1[9],\
                '$\sigma_{x_{2}}$':vP.sigma_x_2[9], '$D_{h}$':None, '$\mu_{h_{1}}$': 13, '$\mu_{h_{2}}$': 13,\
                '$\sigma_{h_{1}}$':0, '$\sigma_{h_{2}}$':0,'$\delta_{\mu_{h}}$':0,'beta': None}]

            packed_parameters.append(paramObjects(fixed_params=fixed_params,vP_=vP,data_columns=copy.copy(data_columns),path=path,fixed_params_column=fixed_params_column))
    elif uniformM:
        for n in vP.num_opts[:5]:
            fixed_params_column = ['n','$D_{m}$','$\mu_{m_{1}}$','$\mu_{m_{2}}$','$\sigma_{m_{1}}$','$\sigma_{m_{2}}$',\
                '$D_{x}$','$\mu_{x_{1}}$','$\mu_{x_{2}}$','$\sigma_{x_{1}}$','$\sigma_{x_{2}}$',\
                '$D_{h}$','$\mu_{h_{1}}$','$\mu_{h_{2}}$','$\sigma_{h_{1}}$','$\sigma_{h_{2}}$','$\delta_{\mu_{h}}$','beta'] 
            fixed_params = [{'n': n, '$D_{m}$':vP.Dm[0],'$\mu_{m_{1}}$':vP.mu_m_1[1],'$\mu_{m_{2}}$':vP.mu_m_2[1],\
                '$\sigma_{m_{1}}$':vP.sigma_m_1[0],'$\sigma_{m_{2}}$':vP.sigma_m_2[0],'$D_{x}$':vP.Dx[0],\
                '$\mu_{x_{1}}$':vP.mu_x_1[99],'$\mu_{x_{2}}$':vP.mu_x_2[99],'$\sigma_{x_{1}}$':vP.sigma_x_1[9],\
                '$\sigma_{x_{2}}$':vP.sigma_x_2[9], '$D_{h}$':None, '$\mu_{h_{1}}$': 13, '$\mu_{h_{2}}$': 13,\
                '$\sigma_{h_{1}}$':0, '$\sigma_{h_{2}}$':0,'$\delta_{\mu_{h}}$':0,'beta': None}]

            packed_parameters.append(paramObjects(fixed_params=fixed_params,vP_=vP,data_columns=copy.copy(data_columns),path=path,fixed_params_column=fixed_params_column))


    
    parallel(partial(looper,vP = vP),packed_parameters)
    # looper(P,vP)

    # parallel(partial(looper,copy.copy(P),vP,path))
