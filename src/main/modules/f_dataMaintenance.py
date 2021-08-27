'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''
def function(pyAAS, *args):
    ''' Data Store Maintenance, for every 1 minutes this modules
        takes a copy of the assetDataTable, deletes from the 
        table values and moves the copy to  the cloud databasse
    '''
    pyAAS.dataStoreManager.assetDataStoreBackup()
