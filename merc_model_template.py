def soc_soh_model( raw_data : {}, average_data : [] ):
    """Filter function to indicate the condition status of battery

    Args:
        raw_data ([dict]): a dictionary contains one or many subset of data.
                        Each subset holds an array of 64 array signal samples
        average_data ([array]): an array (512) of avg data with bandpass filter

    Raises:
        ValueError: use try-catch to handle in high-level app

    Returns:
        [float]: soh, soc value
    """

    '''
    -------------------- Structure of the data schema --------------------------
    raw_data = {
        'adc-ch-a' : [ [raw_sig_1], [raw_sig_2], ... [raw_sig_64] ],
        'adc-ch-b' : [ [raw_sig_1], [raw_sig_2], ... [raw_sig_64] ]             #not available for mercedes demo
    }

    average_data = [512 data pts]
    '''

    print (raw_data['adc-ch-a'])
    print (average_data)

    condition = getCondition(average_data)                                                            # TO-DO Run your code here.

    if condition == 'ok':
        soh_pred, soc_pred = gradient_boosting_multi(average_data)
        return soh_pred, soc_pred
    elif condition == 'warning':    #added Group2: run model with warning
        print('Warning: Inconsistent Measurement Detected') #please change message to desired
        soh_pred, soc_pred = gradient_boosting_multi(average_data)
        return soh_pred, soc_pred
    elif condition == 'critical':
        return -1, -1
    else:
        raise ValueError

def getCondition(average_data):
    condition='ok'
    X_test=average_data[61:] #get signal section after 5us
    minPeak=X_test.min() # get amplitude of abs.min, max of signal
    maxPeak=X_test.max()
    if -0.35<minPeak<0 and 0<maxPeak<0.35:
        condition='critical'
        return condition
    elif -0.5<=minPeak<=-0.35 and 0.35<=maxPeak<=0.45:
        condition='warning'
        return condition
    elif minPeak<-0.5 and 0.45<maxPeak:
        condition='ok'
        return condition
    else:
        raise ValueError

# gradient boosting regression model for predicting soh, soc simultaneously
# average_data is a (nx512) array with n>=1, if n>1, the mean of all predicted values are returned
def gradient_boosting_multi(average_data):
    # define X_test
    X_test=np.asarray(average_data)
    # load model
    with open('internalDemo.pickle.dat', 'rb') as f:
        load_model=pickle.load(f, encoding='latin1')
    f.close()
    # get predictions
    allPrediction=[]
    for row in X_test:
        y_pred=load_model.predict(row.reshape(1,-1))
        allPrediction.append(y_pred)
    # get predicted soh, soc
    #pred_median=np.median(allPrediction, axis=0)
    pred_mean=np.mean(allPrediction, axis=0)
    soh_mean=pred_mean[0][0]
    soc_mean=pred_mean[0][1]
    soh_pred=round(soh_mean,2)
    soc_pred=round(soc_mean,2)
    print('predicted soh: ', soh_pred)
    print('predicted soc: ', soc_pred)
    return soh_pred, soc_pred
