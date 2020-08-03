import pandas as pd
import numpy as np
import time
from sklearn.metrics import r2_score
from scipy.optimize import curve_fit
from scipy.optimize import leastsq
import scipy.optimize as opt
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

from sklearn.kernel_ridge import KernelRidge
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
import gc

from sklearn.model_selection import LeaveOneOut
from sklearn.model_selection import GridSearchCV 
from sklearn.preprocessing import MinMaxScaler
import os

import scipy as sp
np.random.seed(123)

_FOLDER = "/home/acq18mk/master/results/results/"
# _FOLDER = "../results/"

### Coding Part

with open(_FOLDER + "drug_ids_50.txt", 'r') as f:
    drug_ids_50 = [np.int32(line.rstrip('\n')) for line in f]
    
#columns to normalise:
with open(_FOLDER+"columns_to_normalise.txt", 'r') as f:
    columns_to_normalise = [line.rstrip('\n') for line in f]
# *****************************************

with open(_FOLDER+"X_features_cancer_cell_lines.txt", 'r') as f:
    X_cancer_cell_lines = [line.rstrip('\n') for line in f]
# *****************************************

with open(_FOLDER+"X_PubChem_properties.txt", 'r') as f:
    X_PubChem_properties = [line.rstrip('\n') for line in f]
# *****************************************

with open(_FOLDER+"X_features_Targets.txt", 'r') as f:
    X_targets = [line.rstrip('\n') for line in f]
# *****************************************

with open(_FOLDER+"X_features_Target_Pathway.txt", 'r') as f:
    X_target_pathway = [line.rstrip('\n') for line in f]
# *****************************************

all_columns = X_cancer_cell_lines + X_PubChem_properties + X_targets + X_target_pathway +["MAX_CONC"]

train_df = pd.read_csv(_FOLDER+"train08_merged_fitted_sigmoid4_123_with_drugs_properties_min10.csv").drop(["Unnamed: 0","Unnamed: 0.1"], axis=1)
test_df = pd.read_csv(_FOLDER+"test02_merged_fitted_sigmoid4_123_with_drugs_properties_min10.csv").drop(["Unnamed: 0","Unnamed: 0.1"], axis=1)               

train_df_50 = train_df.set_index("DRUG_ID").loc[drug_ids_50, :].copy()
test_df_50 = test_df.set_index("DRUG_ID").loc[drug_ids_50, :].copy()

datasets = ["Dataset 1", "Dataset 2", "Dataset 3", "Dataset 4"]

X_feat_dict = {"Dataset 1": X_cancer_cell_lines ,
               "Dataset 2": ["MAX_CONC"] + X_targets + X_target_pathway + X_cancer_cell_lines ,
               "Dataset 3": ["MAX_CONC"] + X_PubChem_properties +  X_cancer_cell_lines,
               "Dataset 4": ["MAX_CONC"] + X_PubChem_properties +  X_targets + X_target_pathway + X_cancer_cell_lines}

### Coefficient_1

print("Coefficient_1 ....")

print("Linear KernelRidge")

param_tested_alphas = [0.01, 0.1, 0.5, 1, 5, 10, 50, 100, 300, 500]
param_grid = dict(alpha = param_tested_alphas)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel= "linear"), param_grid=param_grid, cv=splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_1"].values
    y_test_drug =  test_drug["param_1"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "linear", alpha=grid.best_params_["alpha"])
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"Linear_KernelRidge_coef1.csv")

print("Sigmoid KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "sigmoid"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_1"].values
    y_test_drug =  test_drug["param_1"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "sigmoid", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"Sigmoid_KernelRidge_coef1.csv")

print("RBF KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "rbf"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_1"].values
    y_test_drug =  test_drug["param_1"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "sigmoid", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"RBF_KernelRidge_coef1.csv")

print("Polynomial KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]
param_tested_degree = [1, 2, 3, 4, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "polynomial"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_1"].values
    y_test_drug =  test_drug["param_1"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "polynomial", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"], degree = grid.best_params_["degree"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "best_degree" + str(i)] = grid.best_params_["degree"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"PolynomialKernelRidge_coef1.csv")

### Coefficient_2

print("Coefficient_2 ....")

print("Linear KernelRidge")

param_tested_alphas = [0.01, 0.1, 0.5, 1, 5, 10, 50, 100, 300, 500]
param_grid = dict(alpha = param_tested_alphas)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel= "linear"), param_grid=param_grid, cv=splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_2"].values
    y_test_drug =  test_drug["param_2"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "linear", alpha=grid.best_params_["alpha"])
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"Linear_KernelRidge_coef2.csv")

print("Sigmoid KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "sigmoid"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_2"].values
    y_test_drug =  test_drug["param_2"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "sigmoid", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"Sigmoid_KernelRidge_coef2.csv")

print("RBF KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "rbf"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_2"].values
    y_test_drug =  test_drug["param_2"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "sigmoid", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"RBF_KernelRidge_coef2.csv")

print("Polynomial KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]
param_tested_degree = [1, 2, 3, 4, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "polynomial"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_2"].values
    y_test_drug =  test_drug["param_2"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "polynomial", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"], degree = grid.best_params_["degree"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "best_degree" + str(i)] = grid.best_params_["degree"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"PolynomialKernelRidge_coef2.csv")

### Coefficient_3

print("Coefficient_3 ....")

print("Linear KernelRidge")

param_tested_alphas = [0.01, 0.1, 0.5, 1, 5, 10, 50, 100, 300, 500]
param_grid = dict(alpha = param_tested_alphas)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel= "linear"), param_grid=param_grid, cv=splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_3"].values
    y_test_drug =  test_drug["param_3"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "linear", alpha=grid.best_params_["alpha"])
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"Linear_KernelRidge_coef3.csv")

print("Sigmoid KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "sigmoid"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_3"].values
    y_test_drug =  test_drug["param_3"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "sigmoid", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"Sigmoid_KernelRidge_coef3.csv")

print("RBF KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "rbf"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_3"].values
    y_test_drug =  test_drug["param_3"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "sigmoid", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"RBF_KernelRidge_coef3.csv")

print("Polynomial KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]
param_tested_degree = [1, 2, 3, 4, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "polynomial"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_3"].values
    y_test_drug =  test_drug["param_3"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "polynomial", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"], degree = grid.best_params_["degree"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "best_degree" + str(i)] = grid.best_params_["degree"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"PolynomialKernelRidge_coef3.csv")

### Coefficient_4

print("Coefficient_4 ....")

print("Linear KernelRidge")

param_tested_alphas = [0.01, 0.1, 0.5, 1, 5, 10, 50, 100, 300, 500]
param_grid = dict(alpha = param_tested_alphas)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel= "linear"), param_grid=param_grid, cv=splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_4"].values
    y_test_drug =  test_drug["param_4"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "linear", alpha=grid.best_params_["alpha"])
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"Linear_KernelRidge_coef4.csv")

print("Sigmoid KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "sigmoid"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_4"].values
    y_test_drug =  test_drug["param_4"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "sigmoid", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"Sigmoid_KernelRidge_coef4.csv")

print("RBF KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "rbf"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_4"].values
    y_test_drug =  test_drug["param_4"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "sigmoid", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"RBF_KernelRidge_coef4.csv")

print("Polynomial KernelRidge")

param_tested_alphas = [0.1, 0.5, 1, 5, 10, 50, 100, 500]
param_tested_gamma = [0.00001, 0.0001, 0.01, 0.1, 1]
param_tested_coef0 = [0.01, 0.1, 0.5, 1, 5]
param_tested_degree = [1, 2, 3, 4, 5]

param_grid = dict(alpha = param_tested_alphas, gamma = param_tested_gamma, coef0 = param_tested_coef0)

splitter_loo = LeaveOneOut()
grid = GridSearchCV(KernelRidge(kernel = "polynomial"), param_grid = param_grid, cv = splitter_loo)

results = pd.DataFrame(index = drug_ids_50)

for drug_id in drug_ids_50:
    drug_name = train_df_50.loc[drug_id, "Drug_Name"].values[0]
    print(drug_id, drug_name)
    train_drug = train_df_50.loc[drug_id,:]
    test_drug = test_df_50.loc[drug_id,:]
    y_train_drug = train_drug["param_4"].values
    y_test_drug =  test_drug["param_4"].values
    
    for i, data_set in list(enumerate(datasets)):
        X_columns = X_feat_dict[data_set]
        scaler = MinMaxScaler().fit(train_drug[X_columns])
        Xtrain_drug = scaler.transform(train_drug[X_columns])
        grid.fit(Xtrain_drug, y_train_drug)
        
         # Pick the best parameterds, train again and predict on the test data
        model = KernelRidge(kernel = "polynomial", alpha=grid.best_params_["alpha"], gamma = grid.best_params_["gamma"],
                           coef0= grid.best_params_["coef0"], degree = grid.best_params_["degree"])
        
        model.fit(Xtrain_drug, y_train_drug)
        Xtest_drug = scaler.transform(test_drug[X_columns])
        
        y_pred = model.predict(Xtest_drug)    
        mse = mean_squared_error(y_test_drug, y_pred)
        mae = mean_absolute_error(y_test_drug, y_pred)
        
        results.loc[drug_id, "best_alpha" + str(i)] = grid.best_params_["alpha"]
        results.loc[drug_id, "best_gamma" + str(i)] = grid.best_params_["gamma"]
        results.loc[drug_id, "best_coef0" + str(i)] = grid.best_params_["coef0"]
        results.loc[drug_id, "best_degree" + str(i)] = grid.best_params_["degree"]
        results.loc[drug_id, "mae_" + str(i)] = mae
        results.loc[drug_id, "mse_" + str(i)] = mse
    del train_drug
    del test_drug

results.to_csv(_FOLDER+"PolynomialKernelRidge_coef4.csv")