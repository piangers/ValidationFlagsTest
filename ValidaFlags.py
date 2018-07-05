# -*- coding: utf-8 -*-

from qgis.core import QGis, QgsVectorLayer, QgsVectorLayer, QgsMapLayerRegistry, QgsFeature, QgsField, QgsGeometry, QGis, QgsSimpleMarkerSymbolLayerV2, QgsLineSymbolV2, QgsMarkerSymbolV2, QgsMarkerLineSymbolLayerV2, QgsSimpleMarkerSymbolLayerBase, QgsSingleSymbolRendererV2
from PyQt4.QtGui import QIcon, QAction, QColor
from PyQt4.QtCore import QObject, SIGNAL, QVariant
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
import resources_rc  
from qgis.gui import QgsMessageBar
from StartNotSimple import StartNotSimple
from StartTestIntersection import StartTestIntersection
from StartOutofBoundsAngles import StartOutofBoundsAngles
from StartDuplic import StartDuplic

class ValidaFlags:

    def __init__(self, iface):
        
        self.iface = iface

        self.tableSchema = 'edgv'
        self.geometryColumn = 'geom'
        self.keyColumn = 'id'
        self.angle = 10
        
    def initGui(self): 
        # cria uma ação que iniciará a configuração do plugin 
        pai = self.iface.mainWindow()
        icon_path = ':/plugins/ValidaFlags/icon.png'
        self.action = QAction (QIcon (icon_path),u"Acessa banco de dados para encontrar erros de validação.", pai)
        self.action.setObjectName ("Validation Flags test ")
        self.action.setStatusTip(None)
        self.action.setWhatsThis(None)
        # Adicionar o botão icone
        self.iface.addToolBarIcon (self.action)

        # SLOTS
        self.action.triggered.connect(self.validate)

    def unload(self):
        # remove o item de ícone do QGIS GUI.
        self.iface.removeToolBarIcon (self.action)


    def validate(self):

        self.layer = self.iface.activeLayer()

        if not self.layer:
            self.iface.messageBar().pushMessage("Erro", u"Esperando uma Active Layer!", level=QgsMessageBar.CRITICAL, duration=4)
            return
        if self.layer.featureCount() == 0:
            self.iface.messageBar().pushMessage("Erro", u"a camada não possui feições!", level=QgsMessageBar.CRITICAL, duration=4)
            return

        self.notSimple = StartNotSimple(self.iface, self.layer)
        self.intersect = StartTestIntersection(self.iface, self.layer)
        self.outOfBounds = StartOutofBoundsAngles(self.iface, self.layer)
        self.duplicate = StartDuplic(self.iface, self.layer)

        flagId = self.notSimple.run(0)
        flagId = self.intersect.run(flagId)
        flagId = self.outOfBounds.run(flagId)
        flagId = self.duplicate.run(flagId)

        self.iface.messageBar().pushMessage("Aviso", "foram geradas " + str(flagId) + " flags para a camada \"" + self.layer.name() + "\" !", level=QgsMessageBar.INFO, duration=4)