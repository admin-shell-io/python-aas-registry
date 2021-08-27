'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

class AAS_Database_Server(object):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
        self.AASRegistryDatabase = self.pyAAS.aasConfigurer.dataBaseFile
    
    def createNewDataBaseColumn(self,colName):
        if colName in self.AASRegistryDatabase:
            return colName
        else:
            self.AASRegistryDatabase[colName] =  []
            return colName
        
    
    def insert_one(self,colName,insertData):
        self.AASRegistryDatabase[colName].append(insertData)
        self.pyAAS.aasConfigurer.saveToDatabase(self.AASRegistryDatabase)
    
    def remove(self,colName,query):
        try:
            databaseColumn =  self.AASRegistryDatabase[colName]
            if "$or" in query:
                queryTerms = query["$or"]
                i = 0 
                for databaseRow in databaseColumn:
                    for queryTerm in queryTerms:
                        for key in queryTerm:
                            if (queryTerm[key] == databaseRow[key]):
                                del self.AASRegistryDatabase[colName][i]
                                return { "message": "success"}
                    i = i + 1
                return {"message":"failure","data":"error"}
            
            if "$and" in query:
                queryTerms = query["$and"]
                checkLength = len(queryTerms)
                for databaseRow in databaseColumn:
                    i = 0
                    for queryTerm in queryTerms:
                        for key in queryTerm:
                            queryTerm[key] = databaseRow[key]
                            i = i + 1
                    if (i == checkLength):
                        del self.AASRegistryDatabase[colName][i]
                        return {"message": "success"}
                    else : 
                        return {"message":"failure","data":"error"}
                return {"message":"failure","data":"error"}    
        except:
            return {"message":"error","data":"error"}

    
    def find(self,colName,query):
        try:
            databaseColumn =  self.AASRegistryDatabase[colName]
            
            if "$or" in query:
                queryTerms = query["$or"]
                for databaseRow in databaseColumn:
                    for queryTerm in queryTerms:
                        for key in queryTerm:
                            if ( queryTerm[key] == databaseRow[key] and queryTerm[key] != ""):
                                return {"data" :databaseRow, "message": "success"}
                return {"data":"Not found","message":"failure"}
            
            elif "$and" in query:
                queryTerms = query["$and"]
                checkLength = len(queryTerms)
                for databaseRow in databaseColumn:
                    i = 0
                    for queryTerm in queryTerms:
                        for key in queryTerm:
                            if (queryTerm[key] ==  databaseRow[key] and queryTerm[key] != ""):
                                i = i + 1
                    if (i == checkLength):
                        return {"data" :databaseRow, "message": "success"}
                    else : 
                        return {"message":"Database Error","data":"error"}
                return {"data":"Not found","message":"failure"}
            
            elif len(query.keys()) == 0:
                if (len(databaseColumn) == 0):
                    return {"data":"Not found","message":"failure"}
                else:
                    return {"message":"success","data":databaseColumn}
            
            else:
                return {"data":"Not found","message":"failure"}
        except Exception as E:
            return {"data":"Not found","message":"error"}
        