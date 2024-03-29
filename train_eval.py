import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score
from sklearn.impute import KNNImputer

"""
Type: Class
Name: TrainModel
Purpose: Class to contain methods related to training and evaluating the random forest classifier
Parameters: Pandas dataframe, threshold (Int), randomizer seed value (Int)
---------------------------------------------------------------------------------------------------------------------------------
Type: Function
Name: load_data
Purpose: Function to load dataframe, find all rows that are not missing values in any feature, randomly take 3000 of those and 
         make them the training set. The rest of them will be the testing set
Parameters: None
Output: None
---------------------------------------------------------------------------------------------------------------------------------
Type: Function
Name: train_model
Purpose: Training the random forest classifier using X_train and y_train
Parameters: None
Output: Trained random forest classifier
---------------------------------------------------------------------------------------------------------------------------------
Type: Function
Name: evaluate_model
Purpose: Evaludate the model by using the test set which contains items with missing values in one or more features. 
         The methods used for abstention, majority class imputation, omit features with missing values, using the mean to 
         imput, using the median to imput and using KNN imputation
Parameters: None
Output: 2 dictionaries of accuracies, one using the entire test set and one only using the items with missing values
"""

class TrainModel:

    def __init__(self, data, threshold = 0.5, random_seed = 0):

        self.data = data
        self.threshold = threshold
        self.random_seed = random_seed
        self.model = RandomForestClassifier(random_state = random_seed)
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None
        self.x_missing = None
        self.y_missing = None
        self.missing = None
        self.accuracy_dict_entire_test_set = {}
        self.accuracy_dict_missing_values = {}
        self.feature_labels = None
        self.columns_missing = None

    def load_data(self):

        data = self.data.copy() #create a copy of the data so that we do not modify the original data in any way
        feature_labels = data.columns.tolist()
        feature_labels.pop(0)
        self.feature_labels = feature_labels
        Xy = data.to_numpy()
        X = Xy[:,1:]
        y = (Xy[:,0] >= self.threshold).astype(int) #sets to 0 if star and 1 if galaxy
        missing = np.sum(np.isnan(X), axis = 1) > 0
        self.x_train, self.x_test, self.y_train, self.y_test = \
            train_test_split(X[~missing], y[~missing], train_size = 3000, random_state = self.random_seed) #only use the items with no missing values
        self.x_missing = X[missing]
        self.y_missing = y[missing]
        self.missing = missing
        missing_values = data.isnull().any()
        columns_missing = data.columns[missing_values].tolist()
        self.columns_missing = columns_missing

    def train_model(self):

        self.model.fit(self.x_train, self.y_train)

        return self.model

    def evaluate_model(self):
        
        method = ['A','B','C','D','E','F'] #create a simple list so that we can iterate through each method one at a time

        for method in method:

            x_test = self.x_test.copy() #generate a copy of test x and y
            y_test = self.y_test.copy()
            x_missing = self.x_missing.copy() #generate a copy of test x and y with missing values
            y_missing = self.y_missing.copy()
            
            if method == 'A': #method: Abstention

                y_test_full = np.concatenate((y_test, y_missing)) #concatenate y test and y with missing items
                y_pred = self.model.predict(x_test) 
                num_missing_items = x_missing.shape[0]
                y_pred_missing = np.full((num_missing_items,), -1)
                y_pred_full = np.concatenate((y_pred, y_pred_missing))
            
                accuracy = accuracy_score(y_test_full, y_pred_full)
                self.accuracy_dict_entire_test_set[method] = accuracy

                #because items with missing values are treated as errors, we can ignore it and give it a 0.0 accuracy
                missing_items_array = np.full((num_missing_items, ), -1) 
                accuracy_missing = accuracy_score(y_missing, missing_items_array)
                self.accuracy_dict_missing_values[method] = accuracy_missing

                print("Method A succeeded")
            
            if method == 'B': #majority inference

                majority_class = np.bincount(self.y_train).argmax() #gets the majority class here

                #create a new np array that is of dimension y_missing but filled with the majority class label
                y_pred_majority = np.full_like(y_missing, fill_value = majority_class) 
                y_pred_non_missing = self.model.predict(x_test)
                y_pred = np.concatenate((y_pred_non_missing, y_pred_majority))
                accuracy = accuracy_score(y_test_full, y_pred)
                self.accuracy_dict_entire_test_set[method] = accuracy

                #missing only now
                #we compare y_pred_majority predictions with y_missing
                accuracy_missing = accuracy_score(y_missing, y_pred_majority)
                self.accuracy_dict_missing_values[method] = accuracy_missing

                print("Method B succeeded")
            
            if method == 'C':
            # omit any features with missing values (based on report generated, the features to be eliminated should be
            # )
                x_test_full = np.concatenate((x_test, x_missing))
                y_test_full = np.concatenate((y_test, y_missing))
                labels_C = self.feature_labels.copy()
                rebuilt_x_test = pd.DataFrame(x_test_full, columns = labels_C)
                rebuilt_x_test = rebuilt_x_test.drop(columns = self.columns_missing, axis = 1) #omitting features with missing values here from the testing set
                x_train = self.x_train.copy()
                y_train = self.y_train.copy() 
                #shouldn't require a copy for y_train, but for the sake of the next two methods, 
                #we'll use copy to prevent accidental modifications to the base truth label set
                rebuilt_x_train = pd.DataFrame(x_train, columns = labels_C)
                rebuilt_x_train = rebuilt_x_train.drop(columns = self.columns_missing, axis = 1) #omitting from training set
                model = RandomForestClassifier(random_state = self.random_seed)
                model.fit(rebuilt_x_train, y_train)

                y_pred = model.predict(rebuilt_x_test)
                accuracy = accuracy_score(y_test_full, y_pred)
                self.accuracy_dict_entire_test_set[method] = accuracy

                rebuilt_x_missing = pd.DataFrame(x_missing, columns = labels_C)
                rebuilt_x_missing = rebuilt_x_missing.drop(columns = self.columns_missing, axis = 1)
                y_pred_missing = model.predict(rebuilt_x_missing)
                accuracy_missing = accuracy_score(y_missing, y_pred_missing)
                self.accuracy_dict_missing_values[method] = accuracy_missing

                print("Method C suceeded")

            if method == 'D': #mean imputation

                feature_labels = self.feature_labels.copy()
                rebuilt_x_missing = pd.DataFrame(x_missing, columns = feature_labels)
                x_train = self.x_train.copy()
                rebuilt_x_train = pd.DataFrame(x_train, columns = feature_labels)
                mean_feature_dict = {}

                for column in self.columns_missing:

                    mean_feature_dict[column] = rebuilt_x_train[column].mean() #get the mean of each column

                for column in mean_feature_dict:

                    rebuilt_x_missing[column] = rebuilt_x_missing[column].fillna(mean_feature_dict[column]) #fill the null values with the mean

                x_test_full = np.concatenate((x_test, rebuilt_x_missing))
                y_test_full = np.concatenate((y_test, y_missing))

                y_pred = self.model.predict(x_test_full)
                accuracy = accuracy_score(y_test_full, y_pred)
                self.accuracy_dict_entire_test_set[method] = accuracy

                y_pred_missing = self.model.predict(rebuilt_x_missing.values)
                accuracy_missing = accuracy_score(y_missing, y_pred_missing)
                self.accuracy_dict_missing_values[method] = accuracy_missing

                print("Method D succeeded")
            
            if method == 'E': #median imputation

                feature_labels = self.feature_labels.copy()
                rebuilt_x_missing = pd.DataFrame(x_missing, columns = feature_labels)
                x_train = self.x_train.copy()
                rebuilt_x_train = pd.DataFrame(x_train, columns = feature_labels)
                median_feature_dict = {}

                for column in self.columns_missing:

                    median_feature_dict[column] = rebuilt_x_train[column].median() #we're doing the same as D but we're using medians

                for column in median_feature_dict:

                    rebuilt_x_missing[column] = rebuilt_x_missing[column].fillna(median_feature_dict[column])

                x_test_full = np.concatenate((x_test, rebuilt_x_missing))
                y_test_full = np.concatenate((y_test, y_missing))

                y_pred = self.model.predict(x_test_full)
                accuracy = accuracy_score(y_test_full, y_pred)
                self.accuracy_dict_entire_test_set[method] = accuracy

                y_pred_missing = self.model.predict(rebuilt_x_missing.values)
                accuracy_missing = accuracy_score(y_missing, y_pred_missing)
                self.accuracy_dict_missing_values[method] = accuracy_missing

                print("Method E succeeded")

            if method == 'F': #KNN imputation
                
                x_train = self.x_train.copy()
                y_test_full = np.concatenate((y_test, y_missing))
                knn_imputer = KNNImputer(n_neighbors = 30)
                knn_imputer.fit(x_train)
                x_missing_imputed = knn_imputer.transform(x_missing)
                x_test_full = np.concatenate((x_test, x_missing_imputed))
                y_pred = self.model.predict(x_test_full)
                accuracy = accuracy_score(y_test_full, y_pred)
                self.accuracy_dict_entire_test_set[method] = accuracy

                y_pred_missing = self.model.predict(x_missing_imputed)
                accuracy_missing = accuracy_score(y_missing, y_pred_missing)
                self.accuracy_dict_missing_values[method] = accuracy_missing

                print("Method F succeeded")

            else:
                continue
        
        




                    
























                



