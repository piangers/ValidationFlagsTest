# -*- coding: utf-8 -*-

from qgis.core import QGis, QgsVectorLayer, QgsVectorLayer, QgsMapLayerRegistry, QgsFeature, QgsField, QgsGeometry, QGis, QgsSimpleMarkerSymbolLayerV2, QgsLineSymbolV2, QgsMarkerSymbolV2, QgsMarkerLineSymbolLayerV2, QgsSimpleMarkerSymbolLayerBase, QgsSingleSymbolRendererV2
from PyQt4.QtGui import QIcon, QAction, QColor
from PyQt4.QtCore import QObject, SIGNAL, QVariant
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
import resources_rc  
from qgis.gui import QgsMessageBar

class StartTestIntersection:

    def __init__(self, iface, layer):
        
        self.iface = iface

        self.layer = layer
        self.tableSchema = 'edgv'
        self.geometryColumn = 'geom'
        self.keyColumn = 'id'


    def run(self, fid = 0):

    ##################################
    ###### PEGA A LAYER ATIVA ########
    ##################################

        parametros = self.layer.source().split(" ") # recebe todos os parametros em uma lista ( senha, porta, password etc..)

    ####################################
    ###### INICIANDO CONEXÃO DB ########
    ####################################

        # Outra opção para isso, seria usar ex: self.dbname.. self.host.. etc.. direto dentro do laço for.
        dbname = "" 
        host = ""
        port = 0
        user = ""
        password = ""

        for i in parametros:
            part = i.split("=")
            
        # Recebe os parametros guardados na própria Layer

            if "dbname" in part[0]:
                dbname = part[1].replace("'", "")

            elif "host" in part[0]:
                host = part[1].replace("'", "")

            elif "port" in part[0]:
                port = int(part[1].replace("'", ""))

            elif "user" in part[0]:
                user = part[1].replace("'", "")

            elif "password" in part[0]:
                password = part[1].split("|")[0].replace("'", "")

        
        print dbname, host, port, user, password

        # Testa se os parametros receberam os valores pretendidos, caso não, apresenta a mensagem informando..
        if len(dbname) == 0 or len(host) == 0 or port == 0 or len(user) == 0 or len(password) == 0:
            self.iface.messageBar().pushMessage("Erro", u'Um dos parametros não foram devidamente recebidos!', level=QgsMessageBar.CRITICAL, duration=4)
            return

    ####################################
    #### SETA VALORES DE CONEXÃO DB ####
    ####################################

        connection = QSqlDatabase.addDatabase('QPSQL')
        connection.setHostName(host)
        connection.setPort(port)
        connection.setUserName(user)
        connection.setPassword(password)
        connection.setDatabaseName(dbname)

        if not connection.isOpen(): # Testa se a conexão esta recebendo os parametros adequadamente.
            if not connection.open():
                print 'Error connecting to database!'
                self.iface.messageBar().pushMessage("Erro", u'Error connecting to database!', level=QgsMessageBar.CRITICAL, duration=4)
                print connection.lastError().text()
                return

    ####################################
    ###### CRIAÇÃO DE MEMORY LAYER #####
    ####################################
        

        layerCrs = self.layer.crs().authid() # Passa o formato (epsg: numeros)

        flagsLayerName = self.layer.name() + "_flags"
        flagsLayerExists = False

        for l in QgsMapLayerRegistry.instance().mapLayers().values(): # Recebe todas as camadas que estão abertas
            if l.name() == flagsLayerName: # ao encontrar o nome pretendido..
                self.flagsLayer = l # flagslayer vai receber o nome..
                self.flagsLayerProvider = l.dataProvider()
                flagsLayerExists = True # se encontrado os parametros buscados, recebe True.
                break
        
        if flagsLayerExists == False: # se não encontrado os parametros buscados, recebe False.
            tempString = "Point?crs="
            tempString += str(layerCrs)

            self.flagsLayer = QgsVectorLayer(tempString, flagsLayerName, "memory")
            self.flagsLayerProvider = self.flagsLayer.dataProvider()
            self.flagsLayerProvider.addAttributes([QgsField("flagId", QVariant.String), QgsField("geomId", QVariant.String), QgsField("motivo", QVariant.String)])
            self.flagsLayer.updateFields()

        if fid == 0: # Se for 0 então está iniciando e limpa, caso contrário não.
            self.flagsLayer.startEditing()
            ids = [feat.id() for feat in self.flagsLayer.getFeatures()]
            self.flagsLayer.deleteFeatures(ids)
            self.flagsLayer.commitChanges()
        
        
        lista_fid = [] # Iniciando lista
        for f in self.layer.getFeatures():
            lista_fid.append(str(f.id())) # Guarda na lista. A lista de Feature ids passa tipo "int", foi convertido e guardado como "str".

        source = self.layer.source().split(" ")
        self.tableName = "" # Inicia vazio
        layerExistsInDB = False
        
        for i in source:
                
            if "table=" in i or "layername=" in i: # Se encontrar os atributos pretendidos dentre todos do for
                self.tableName = source[source.index(i)].split(".")[1] # Faz split em ponto e pega a segunda parte.
                self.tableName = self.tableName.replace('"', '')
                layerExistsInDB = True
                break
             
        if layerExistsInDB == False:
            self.iface.messageBar().pushMessage("Erro", u"Provedor da camada corrente não provem do banco de dados!", level=QgsMessageBar.CRITICAL, duration=4)
            return
        
        # Busca através do SQL 
        query_string  = '''select distinct (reason(ST_IsValidDetail(f."{2}",0))) AS motivo, '''
        query_string += '''ST_AsText(ST_Multi(ST_SetSrid(location(ST_IsValidDetail(f."{2}",0)), ST_Srid(f.{2})))) as local, '''
        query_string += '''f.{3} as {3} from '''
        query_string += '''(select "{3}", "{2}" from only "{0}"."{1}"  where ST_IsValid("{2}") = 'f' and {3} in ({4})) as f''' 
        query_string  = query_string.format(self.tableSchema, self.tableName, self.geometryColumn, self.keyColumn, ",".join(lista_fid))
        
        query = QSqlQuery(query_string)
        
        self.flagsLayer.startEditing()
        flagCount = fid # iniciando contador que será referência para os IDs da camada de memória.
        
        listaFeatures = []
        while query.next():
            motivo = query.value(0)
            local = query.value(1)
            geomId = query.value(2)
            flagId = str(flagCount)

            flagFeat = QgsFeature()
            flagFeat.setFields(self.flagsLayer.fields()) # passa quais atributos serão usados.
            flagGeom = QgsGeometry.fromWkt(local) # passa o local onde foi localizado o erro.
            flagFeat.setGeometry(flagGeom)
            flagFeat.setAttribute(0, flagId) # insere o id definido para a coluna 0 da layer de memória.
            flagFeat.setAttribute(1, geomId) # insere o motivo/razão pré-definida para a coluna 1 da layer de memória.
            flagFeat.setAttribute(2, motivo) # insere o motivo/razão pré-definida para a coluna 1 da layer de memória.

            listaFeatures.append(flagFeat)    

            flagCount += 1 # incrementando o contador a cada iteração

        self.flagsLayerProvider.addFeatures(listaFeatures)
        self.flagsLayer.commitChanges() # Aplica as alterações à camada.
        
        QgsMapLayerRegistry.instance().addMapLayer(self.flagsLayer) # Adicione a camada no mapa.

        return flagCount
