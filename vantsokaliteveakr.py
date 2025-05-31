import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QFileDialog, QLabel, QWidget, QVBoxLayout, QInputDialog, QScrollArea
from PyQt5.QtCore import Qt, QUrl
from PyQt5 import uic
from PyQt5.QtGui import QDesktopServices
import os
import shutil

Ui_MainWindow, _ = uic.loadUiType("dokudokuman.ui")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Veritabanı bağlantısını oluştur
        self.connection = sqlite3.connect("dokumanlar.db")
        self.cursor = self.connection.cursor()
        self.createTable()

        # UI dosyasını yükle
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Kategori düğümlerini oluştur
        self.createCategoryNodes()
        self.loadDocuments()

        # Sinyal-slot bağlantılarını yap
        self.ui.treeWidget.itemExpanded.connect(self.onItemExpanded)
        self.ui.treeWidget.itemCollapsed.connect(self.onItemCollapsed)
        self.ui.treeWidget.itemDoubleClicked.connect(self.onItemDoubleClicked)
        self.ui.treeWidget.itemClicked.connect(self.openPDF)

        # PDF Ekle butonuna tıklamayı d_2
        self.ui.pushButton_2.clicked.connect(self.addPDF)

        # PDF Görüntüle butonuna tıklamayı dinle
        self.ui.pushButton.clicked.connect(self.viewPDF)

        self.ui.pushButton_3.clicked.connect(self.deleteDocument)

        self.current_category = None
        self.current_tab = self.ui.tabWidget.currentIndex()
        self.ui.tabWidget.currentChanged.connect(self.onTabChanged)
        self.createSubcategoriesForBirimFormlari()

  
        

        # Seçilen dosyanın yolunu görüntülemek için QLabel'ı güncelle
        self.selected_file_label = QLabel(self.ui.centralwidget)
        self.selected_file_label.setAlignment(Qt.AlignRight)
        self.selected_file_label.setGeometry(10, 550, 1001, 16)

        layout = QVBoxLayout(self.ui.centralwidget)
        layout.addWidget(self.ui.tabWidget)

        # If self.ui.pushButton, self.ui.pushButton_2, self.ui.pushButton_3 are already defined in your Ui class,
        # you can directly use them here. If not, create them in the Ui class and then use them here.
        layout.addWidget(self.ui.pushButton)
        layout.addWidget(self.ui.pushButton_2)
        layout.addWidget(self.ui.pushButton_3)
        layout.addWidget(self.selected_file_label)

        # Set the layout of the central widget
        self.ui.centralwidget.setLayout(layout)

        # Set the central widget of the main window
        self.setCentralWidget(self.ui.centralwidget)


    def onTabChanged(self, index):
        # Tab değiştiğinde bu metot çalışacak ve mevcut olarak seçili olan tabı güncelleyecek
        self.current_tab = index    

    def addPDF(self):
        current_tab_index = self.ui.tabWidget.currentIndex()
        current_tree_widget = self.ui.treeWidget if current_tab_index == 0 else self.ui.treeWidget_2
        match current_tab_index: 
            case 0:
                tabname="KKMS"
                current_tree_widget = self.ui.treeWidget
            case 1:
                tabname="MMS"
                current_tree_widget = self.ui.treeWidget_2
            case 2:
                tabname="PD"
                current_tree_widget = self.ui.treeWidget_3
            case 3:
                tabname="CM"
                current_tree_widget = self.ui.treeWidget_4
                
        selected_item = current_tree_widget.currentItem()

        if selected_item and ".pdf" not in selected_item.text(0):
            file_filter = "PDF Dosyaları (*.pdf);;Word Dosyaları (*.doc *.docx);;Excel Dosyaları (*.xls *.xlsx)"
            file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", file_filter)

            if file_path:
                # Dosya adını ve kategoriyi al
                file_name = os.path.basename(file_path)
                kategori = selected_item.text(0)

                # Dosya adı ve kategori bilgisini kullanarak veritabanında böyle bir kayıt var mı kontrol et
                self.cursor.execute("SELECT * FROM Dokumanlar WHERE kategori=? AND ad=? AND sistem=?", (kategori, file_name, tabname))
                existing_doc = self.cursor.fetchone()

                if existing_doc:
                    print("Bu dosya zaten eklenmiş.")
                else:
                    # Veritabanına dosya bilgilerini ekle
                    self.cursor.execute("INSERT INTO Dokumanlar (kategori, ad, dosya_yolu, sistem) VALUES (?, ?, ?, ?)", (kategori, file_name, file_path, tabname))
                    self.connection.commit()
                    print("Doküman veritabanına eklendi.")

                    # Dosyayı "uploads" klasörüne kopyala
                    upload_path = os.path.join("uploads", file_name)
                    shutil.copy(file_path, upload_path)

                    # Dosya adını ağaç yapısına ekleyerek göster
                    dosya_ad_item = QTreeWidgetItem(selected_item)
                    dosya_ad_item.setText(0, file_name)

                    # Kategoriyi açık hale getir
                    selected_item.setExpanded(True)

    def createSubcategoriesForBirimFormlari(self):
        # "Birim Formları" kategorisini bul
        category_item = self.findCategoryNode2("Birim Formları")

        if category_item:
            # Alt kategorileri oluştur ve "Birim Formları" altına ekleyin
            subcategories = ["Ticaret Sicil Müd.", "Planlama Koord. ve Komiteler Müd.", "Mali İşler Müd.", "İ.K. Kalite ve Akrd. Müd.", "Özel Kalem Müd.", "Belgelendirme Müd.", "İdari İşler ve Bilgi İşlem Müd.", "Dış Tic. Birimi", "Eğitim ve Mesleki Sertifikasyon Birimi", "AR-GE ve Sanayi Birimi", "Basın Yayın ve Halkla İlişkiler Koor.", "Proje Koor."]

            for subcategory_name in subcategories:
                subcategory_item = QTreeWidgetItem(category_item)
                subcategory_item.setText(0, subcategory_name)
                subcategory_item.setFlags(subcategory_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

    def findCategoryNodeKKMS(self, category_name):
        for i in range(self.ui.treeWidget.topLevelItemCount()):
            item = self.ui.treeWidget.topLevelItem(i)
            if item.text(0) == category_name:
                return item
        return None

    def findCategoryNodeMMS(self, category_name):
        for i in range(self.ui.treeWidget_2.topLevelItemCount()):
            item = self.ui.treeWidget_2.topLevelItem(i)
            if item.text(0) == category_name:
                return item
        return None

    def createTable(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Dokumanlar
                           (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            kategori TEXT,
                            sistem TEXT,
                            ad TEXT,
                            dosya_yolu TEXT)''')
        self.connection.commit()

    def createCategoryNodes(self):
        #MMS Tabı
        self.createCategoryNode("El Kitapları", self.ui.treeWidget_2)
        self.createCategoryNode("Politikalar", self.ui.treeWidget_2)
        self.createCategoryNode("Prosedürler", self.ui.treeWidget_2)
        self.createCategoryNode("Talimatlar", self.ui.treeWidget_2)
        self.createCategoryNode("Görev Tanımları", self.ui.treeWidget_2)
        self.createCategoryNode("Prosesler", self.ui.treeWidget_2)
        self.createCategoryNode("Genel Formlar", self.ui.treeWidget_2)
        self.createCategoryNode("Birim Formları", self.ui.treeWidget_2)
        self.createCategoryNode("Planlar", self.ui.treeWidget_2)
 
        #KKMS Tabı
        self.createCategoryNode("El Kitapları", self.ui.treeWidget)
        self.createCategoryNode("Politikalar", self.ui.treeWidget)
        self.createCategoryNode("Prosedürler", self.ui.treeWidget)
        self.createCategoryNode("Talimatlar", self.ui.treeWidget)
        self.createCategoryNode("Görev Tanımları", self.ui.treeWidget)
        self.createCategoryNode("Prosesler", self.ui.treeWidget)
        self.createCategoryNode("Formlar", self.ui.treeWidget)

        self.createCategoryNode("Performans Değerlendirme Raporları", self.ui.treeWidget_3)
        self.createCategoryNode("Çalışan Memnuniyeti Raporları", self.ui.treeWidget_4)
        # Diğer kategoriler eklenebilir

    def createCategoryNode(self, category_name, tree_widget):
        # Kategori düğümünü oluştur ve ilgili tab'a ekleyin
        node = QTreeWidgetItem(tree_widget)
        node.setText(0, category_name)
        node.setFlags(node.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

    def onItemExpanded(self, item):
        item.setExpanded(True)

    def onItemCollapsed(self, item):
        item.setExpanded(False)

    def onItemDoubleClicked(self, item, column):
        if item.childCount() == 0:
            # Document node is double-clicked
            file_path, _ = QFileDialog.getOpenFileName(self, "PDF Dosyasını Seç", "", "PDF Dosyaları (*.pdf)")
            if file_path:
                if item.parent() is not None:
                    kategori = item.parent().data(0, Qt.DisplayRole)  # Get the parent item's text
                    ad = item.data(0, Qt.DisplayRole)  # Get the double-clicked item's text
                    self.insertDocument(kategori, ad, file_path)
                else:
                    # No parent (category) for the item, do nothing for now
                    pass

    def openPDF(self, item, column):
        if item.childCount() == 0 and column == 0:
            # Document node is clicked (single-click)
            file_name = item.text(0)
            file_path = os.path.join("uploads", file_name)
            if file_path.lower().endswith('.pdf') and os.path.exists(file_path):
                # Dosyayı açmak yerine sadece seçilen dosyanın yolunu güncelleyin
                self.selected_file_label.setText(file_path)

    def addSubcategory(self):
    # Kullanıcıdan alt kategori adını al
        subcategory_name, ok = QInputDialog.getText(self, "Alt Kategori Ekle", "Alt Kategori Adı:")
        if ok and subcategory_name:
            # "Birim Formları" kategorisinin altına yeni bir alt kategori düğümü oluştur
            category_item = self.findCategoryNode2("Birim Formları")
            if category_item:
                subcategory_item = QTreeWidgetItem(category_item)
                subcategory_item.setText(0, subcategory_name)
                subcategory_item.setFlags(subcategory_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            else:
                print("Kategori bulunamadı.")

    def insertDocument(self, kategori, ad, dosya_yolu, sistem):
        dosya_adi = os.path.basename(dosya_yolu)

        # Dosya adı ve kategori bilgisini kullanarak veritabanında böyle bir kayıt var mı kontrol edelim
        self.cursor.execute("SELECT * FROM Dokumanlar WHERE kategori=? AND ad=? AND sistem=?", (kategori, dosya_adi, sistem))
        existing_doc = self.cursor.fetchone()

        if existing_doc:
            # Bu dosya adı ve kategoriyle zaten bir kayıt var, tekrar eklemeyi engelleyelim
            print("Bu dosya zaten eklenmiş.")
            return

        self.cursor.execute("INSERT INTO Dokumanlar (kategori, ad, dosya_yolu, sistem) VALUES (?, ?, ?, ?)", (kategori, dosya_adi, dosya_yolu, sistem))
        self.connection.commit()
        print("Doküman veritabanına eklendi.")

        # Dosyayı "uploads" adlı klasöre taşıyalım (burada eklemeyi engellemek için silmiyoruz)
        upload_path = os.path.join("uploads", dosya_adi)
        shutil.copy(dosya_yolu, upload_path)

    def viewPDF(self):
        if self.current_tab == 0:
            selected_item = self.ui.treeWidget.currentItem()
        elif self.current_tab == 1:
            selected_item = self.ui.treeWidget_2.currentItem()
        elif self.current_tab == 2:
            selected_item = self.ui.treeWidget_3.currentItem()
        elif self.current_tab == 3:
            selected_item = self.ui.treeWidget_4.currentItem()
        if selected_item and selected_item.childCount() == 0:
            file_name = selected_item.text(0)
            file_path = os.path.join("uploads", file_name)
            if file_path.lower().endswith(('.pdf', '.docx', '.doc', '.xlsx', '.xls')):
            # .pdf, .docx, .doc, .xlsx ve .xls uzantılı dosyaları varsayılan uygulamalarda aç
                self.viewDocument(file_path)
            else:
                print("Dosya bulunamadı veya desteklenmeyen uzantı.")


    def viewDocument(self, file_path):
        if os.path.exists(file_path):
            url = QUrl.fromLocalFile(file_path)
            QDesktopServices.openUrl(url)
        else:
            print("Dosya bulunamadı.")            

    def loadDocuments(self):
    # Veritabanından dokümanları yükle ve ağaç yapısına ekleyin
        self.cursor.execute("SELECT kategori, ad, dosya_yolu, sistem FROM Dokumanlar")
        documents = self.cursor.fetchall()

        for kategori, ad, dosya_yolu, sistem in documents:
            if sistem == "KKMS":
                # Kategori düğümünü bul veya oluştur
                kategori_node = self.findCategoryNode(kategori)

                if not kategori_node:
                    kategori_node = QTreeWidgetItem(self.ui.treeWidget)

                    kategori_node.setText(0, kategori)
                    kategori_node.setFlags(kategori_node.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

                # Dosya düğümünü oluştur ve kategori altına ekleyin
                dosya_ad_node = QTreeWidgetItem(kategori_node)
                dosya_ad_node.setText(0, ad)
            elif sistem=="MMS":
                # MMS Tab
                # Kategori düğümünü bul veya oluştur
                kategori_node = self.findCategoryNode2(kategori)

                if not kategori_node:
                    kategori_node = QTreeWidgetItem(self.ui.treeWidget_2)
                    kategori_node.setText(0, kategori)
                    kategori_node.setFlags(kategori_node.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

                # Dosya düğümünü oluştur ve kategori altına ekleyin
                dosya_ad_node = QTreeWidgetItem(kategori_node)
                dosya_ad_node.setText(0, ad)
            elif sistem=="PD":

                # MMS Tab
                # Kategori düğümünü bul veya oluştur
                kategori_node = self.findCategoryNode3(kategori)

                if not kategori_node:
             
                    kategori_node = QTreeWidgetItem(self.ui.treeWidget_3)
                    kategori_node.setText(0, kategori)
                    kategori_node.setFlags(kategori_node.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            elif sistem=="CM":

                # MMS Tab
                # Kategori düğümünü bul veya oluştur
                kategori_node = self.findCategoryNode4(kategori)
                if not kategori_node:
                    kategori_node = QTreeWidgetItem(self.ui.treeWidget_4)
                    kategori_node.setText(0, kategori)
                    kategori_node.setFlags(kategori_node.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

                # Dosya düğümünü oluştur ve kategori altına ekleyin
                dosya_ad_node = QTreeWidgetItem(kategori_node)
                dosya_ad_node.setText(0, ad)

    def findCategoryNode(self, category_name):
        # Verilen kategori adına sahip düğümü bulun
        for i in range(self.ui.treeWidget.topLevelItemCount()):
            item = self.ui.treeWidget.topLevelItem(i)
            if item.text(0) == category_name:
                return item
        return None
    
    def findCategoryNode2(self, category_name):
        # Verilen kategori adına sahip düğümü bulun
        for i in range(self.ui.treeWidget_2.topLevelItemCount()):
            item = self.ui.treeWidget_2.topLevelItem(i)
            if item.text(0) == category_name:
                return item
        return None
    def findCategoryNode3(self, category_name):
        # Verilen kategori adına sahip düğümü bulun
        for i in range(self.ui.treeWidget_3.topLevelItemCount()):
            item = self.ui.treeWidget_3.topLevelItem(i)
            if item.text(0) == category_name:
                return item
        return None
    def findCategoryNode4(self, category_name):
        # Verilen kategori adına sahip düğümü bulun
        for i in range(self.ui.treeWidget_4.topLevelItemCount()):
            item = self.ui.treeWidget_4.topLevelItem(i)
            if item.text(0) == category_name:
                return item
        return None
        
    def deleteDocument(self):
        selected_item = None
        if self.current_tab == 0:
            # KKMS Tab
            sistem = "KKMS"
            selected_item = self.ui.treeWidget.currentItem()
            parent_widget = self.ui.treeWidget
        elif self.current_tab == 1:
            # MMS Tab
            sistem = "MMS"
            selected_item = self.ui.treeWidget_2.currentItem()
            parent_widget = self.ui.treeWidget_2
        elif self.current_tab == 2:
            # MMS Tab
            sistem = "PD"
            selected_item = self.ui.treeWidget_3.currentItem()
            parent_widget = self.ui.treeWidget_3
        elif self.current_tab == 3:
            # MMS Tab
            sistem = "CM"
            selected_item = self.ui.treeWidget_4.currentItem()
            parent_widget = self.ui.treeWidget_4
        if selected_item and selected_item.childCount() == 0:
            file_name = selected_item.text(0)
          
            file_path = os.path.join("uploads", file_name)
            if os.path.exists(file_path):
                # Veritabanından dokümanı silin
                kategori = selected_item.parent().text(0)
                ad = selected_item.text(0)
                self.cursor.execute("DELETE FROM Dokumanlar WHERE kategori=? AND ad=? AND sistem=?", (kategori, ad, sistem))
                self.connection.commit()

                # Dosyayı "uploads" klasöründen silin
                os.remove(file_path)

                # Ağaç yapısından dosya düğümünü kaldırın
                parent = selected_item.parent()
                if parent:
                    index = parent.indexOfChild(selected_item)
                    parent.takeChild(index)
                else:
                    # If there is no parent, it means the selected item is a top-level category node.
                    # In that case, just remove the selected item from the tree widget.
                    index = parent_widget.indexOfTopLevelItem(selected_item)
                    parent_widget.takeTopLevelItem(index)
            else:
                print("Dosya bulunamadı.")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()