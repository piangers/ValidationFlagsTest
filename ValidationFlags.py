# -*- coding: utf-8 -*-

from qgis.core import QGis, QgsVectorLayer, QgsVectorLayer, QgsMapLayerRegistry, QgsFeature, QgsField, QgsGeometry, QGis, QgsSimpleMarkerSymbolLayerV2, QgsLineSymbolV2, QgsMarkerSymbolV2, QgsMarkerLineSymbolLayerV2, QgsSimpleMarkerSymbolLayerBase, QgsSingleSymbolRendererV2
from PyQt4.QtGui import QIcon, QAction, QColor
from PyQt4.QtCore import QObject, SIGNAL, QVariant
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
import resources_rc  
from qgis.gui import QgsMessageBar
from DsgTools.dsgEnums import DsgEnums

class ValidationFlags:

    def __init__(self, iface):
        
        self.iface = iface

        self.tableSchema = 'edgv'
        self.geometryColumn = 'geom'
        self.keyColumn = 'id'
        self.angle = 10

    def initGui(self): 
        # cria uma ação que iniciará a configuração do plugin 
        pai = self.iface.mainWindow()
        icon_path = ':/plugins/ValidationFlags/icon.png'
        self.action = QAction (QIcon (icon_path),u"Acessa banco de dados para encontrar erros de validação.", pai)
        self.action.setObjectName ("Validation Flags test ")
        self.action.setStatusTip(None)
        self.action.setWhatsThis(None)
        self.action.triggered.connect(self.run)
        # Adicionar o botão icone
        self.iface.addToolBarIcon (self.action) 

    def unload(self):
        # remove o item de ícone do QGIS GUI.
        self.iface.removeToolBarIcon (self.action)



    def loger(self):

    ##################################
    ###### PEGA A LAYER ATIVA ########
    ##################################

        layer = self.iface.activeLayer() 

        if not layer:
            self.iface.messageBar().pushMessage("Erro", u"Esperando uma Active Layer!", level=QgsMessageBar.CRITICAL, duration=4)
            return
        if layer.featureCount() == 0:
            self.iface.messageBar().pushMessage("Erro", u"a camada não possui feições!", level=QgsMessageBar.CRITICAL, duration=4)
            return

        parametros = layer.source().split(" ") # recebe todos os parametros em uma lista ( senha, porta, password etc..)

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

        #print dbname, host, port, user, password

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
        
        layerCrs = layer.crs().authid() # Passa o formato (epsg: numeros)

        flagsLayerName = layer.name() + "_flags"
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
            self.flagsLayerProvider.addAttributes([QgsField("flagId", QVariant.Int), QgsField("geomId", QVariant.String), QgsField("motivo", QVariant.String)])
            self.flagsLayer.updateFields()

        self.flagsLayer.startEditing()
        ids = [feat.id() for feat in self.flagsLayer.getFeatures()]
        self.flagsLayer.deleteFeatures(ids)
        self.flagsLayer.commitChanges()
        
        lista_fid = [] # Iniciando lista
        for f in layer.getFeatures():
            lista_fid.append(str(f.id())) # Guarda na lista. A lista de Feature ids passa tipo "int", foi convertido e guardado como "str".

        source = layer.source().split(" ")
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

        self.sqlAngulo
        self.sqlIntersect
        self.sqlDuplic
        self.sqlNotSimple
        
        query = QSqlQuery(sql)
        
        self.flagsLayer.startEditing()
        flagCount = 0 # iniciando contador que será referência para os IDs da camada de memória.

        listaFeatures = []
        while query.next():
            id = query.value(0)
            local = query.value(1)
            angulo = query.value(2)
            flagId = flagCount

            print id, local, angulo

            flagFeat = QgsFeature()
            flagGeom = QgsGeometry.fromWkt(local) # passa o local onde foi localizado o erro.
            flagFeat.setGeometry(flagGeom)
            #flagFeat.initAttributes(3)
            flagFeat.setAttribute(0,flagId) # insere o id definido para a coluna 0 da layer de memória.
            flagFeat.setAttribute(1, id) # insere o id da geometria  para a coluna 1 da layer de memória.
            
            if self.sqlAngulo:
                flagFeat.setAttribute(2, u"Ângulo para os vértices adjacentes inferior à tolerância")
            if self.sqlDuplic:
                flagFeat.setAttribute(2, u"Duplicação de Geometria")
            if self.sqlIntersect:
                flagFeat.setAttribute(2, u"Interseção de Geometria encontrada")
            if self.sqlNotSimple:
                flagFeat.setAttribute(2, u"Geometria não é simples")

            listaFeatures.append(flagFeat)    

            flagCount += 1 # incrementando o contador a cada iteração

        self.flagsLayerProvider.addFeatures(listaFeatures)
        self.flagsLayer.commitChanges() # Aplica as alterações à camada.
        
        QgsMapLayerRegistry.instance().addMapLayer(self.flagsLayer) # Adicione a camada no mapa
        
        if flagCount == 0: 
            
            QgsMapLayerRegistry.instance().removeMapLayer(self.flagsLayer.id())
            self.iface.messageBar().pushMessage("Aviso", u"Não foi encontrado Flags em \"" + layer.name() + "\" !", level=QgsMessageBar.CRITICAL, duration=4)

            return
        if len(query.lastError().text()) == 1:
            self.iface.messageBar().pushMessage("Aviso", "foram geradas " + str(flagCount) + " flags para a camada \"" + layer.name() + "\" !", level=QgsMessageBar.INFO, duration=4)
        else:
            self.iface.messageBar().pushMessage("Erro", u"a geração de flags falhou!", level=QgsMessageBar.CRITICAL, duration=4)
            print query.lastError().text()

    def sqlAngulo(self,lista_fid):

        geomType = layer.geometryType()

        if geomType == QGis.Line:
            
        # Busca através do SQL 
            sql = """
            WITH result AS (SELECT points."{4}", points.anchor, (degrees
                                        (
                                            ST_Azimuth(points.anchor, points.pt1) - ST_Azimuth(points.anchor, points.pt2)
                                        )::decimal + 360) % 360 as angle
                        FROM
                        (SELECT
                              ST_PointN("{3}", generate_series(1, ST_NPoints("{3}")-2)) as pt1, 
                              ST_PointN("{3}", generate_series(2, ST_NPoints("{3}")-1)) as anchor,
                              ST_PointN("{3}", generate_series(3, ST_NPoints("{3}"))) as pt2,
                              linestrings."{4}" as "{4}" 
                            FROM
                              (SELECT "{4}" as "{4}", (ST_Dump("{3}")).geom as "{3}"
                               FROM only "{0}"."{1}"
                               ) AS linestrings WHERE ST_NPoints(linestrings."{3}") > 2 ) as points)
            select distinct "{4}", ST_AsText(anchor), angle from result where (result.angle % 360) < {2} or result.angle > (360.0 - ({2} % 360.0)) and result.{4} in ({5})""".format( self.tableSchema, self.tableName, self.angle, self.geometryColumn, self.keyColumn,",".join(lista_fid))
        
        elif geomType == QGis.Polygon:
            sql = """
            WITH result AS (SELECT points."{4}", points.anchor, (degrees
                                        (
                                            ST_Azimuth(points.anchor, points.pt1) - ST_Azimuth(points.anchor, points.pt2)
                                        )::decimal + 360) % 360 as angle
                        FROM
                        (SELECT
                              ST_PointN("{3}", generate_series(1, ST_NPoints("{3}")-1)) as pt1,
                              ST_PointN("{3}", generate_series(1, ST_NPoints("{3}")-1) %  (ST_NPoints("{3}")-1)+1) as anchor,
                              ST_PointN("{3}", generate_series(2, ST_NPoints("{3}")) %  (ST_NPoints("{3}")-1)+1) as pt2,
                              linestrings."{4}" as "{4}"
                            FROM
                              (SELECT "{4}" as "{4}", (ST_Dump(ST_Boundary(ST_ForceRHR((ST_Dump("{3}")).geom)))).geom as "{3}"
                               FROM only "{0}"."{1}" 
                               ) AS linestrings WHERE ST_NPoints(linestrings."{3}") > 2 ) as points)
            select distinct "{4}", ST_AsText(anchor), angle from result where (result.angle % 360) < {2} or result.angle > (360.0 - ({2} % 360.0)) and result.{4} in ({5})""".format( self.tableSchema, self.tableName, self.angle, self.geometryColumn, self.keyColumn,",".join(lista_fid) )

            return sql


    def sqlDuplic(self,lista_fid): 
        
        sql = '''select * from (
        SELECT "{3}",
        ROW_NUMBER() OVER(PARTITION BY "{2}" ORDER BY "{3}" asc) AS Row,
        ST_AsText(geom) FROM ONLY "{0}"."{1}" 
        where {3} in ({4})
        ) dups 
        where dups.Row > 1'''.format(self.tableSchema, self.tableName, self.geometryColumn, self.keyColumn, ",".join(lista_fid))

        return sql


    def sqlNotSimple(self,lista_fid):

        sql = """select foo."{3}" as "{3}", ST_AsText(ST_MULTI(st_startpoint(foo."{2}"))) as "{2}" from (
        select "{3}" as "{3}", (ST_Dump(ST_Node(ST_SetSRID(ST_MakeValid("{2}"),ST_SRID("{2}"))))).geom as "{2}" from "{0}"."{1}"  
        where ST_IsSimple("{2}") = 'f' and {3} in ({4})) as foo where st_equals(st_startpoint(foo."{2}"),st_endpoint(foo."{2}"))""".format(self.tableSchema, self.tableName, self.geometryColumn, self.keyColumn, ",".join(lista_fid))

        return sql


    def sqlIntersect(self,lista_fid):
        sql = '''select distinct (reason(ST_IsValidDetail(f."{2}",0))) AS motivo, 
        ST_AsText(ST_Multi(ST_SetSrid(location(ST_IsValidDetail(f."{2}",0)), ST_Srid(f.{2})))) as local from 
        (select "{3}", "{2}" from only "{0}"."{1}"  where ST_IsValid("{2}") = 'f' and {3} in ({4})) as f''' .format(self.tableSchema, self.tableName, self.geometryColumn, self.keyColumn, ",".join(lista_fid))

        return sql
