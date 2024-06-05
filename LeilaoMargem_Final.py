from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
import sys
import re
import easygui
import pandas as pd
import margem
import os
import shutil
import ctypes  

# pip install PyQt5
# pip install easygui
# pip install pandas
# pip install openpyxl


# Ajustar a janela
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

# Melhorias:
# Síncrono fictício: descobrir o nível de tensão automaticamente

class MarginApp(QtWidgets.QMainWindow, margem.Ui_MainWindow):
    def __init__(self, parent=None):
        
        super(MarginApp, self).__init__(parent)
        self.setupUi(self)
        self.deck_DGMT = None
        
        # Ações
        # Abrir Fotólica
        self.abrirFotolica.triggered.connect(self.abrirFotolica1)
        # Abrir caso do Anarede
        self.actionAnarede.triggered.connect(self.actionAnarede1)
        
        # Gerar decks PWF
        self.actionGerar.triggered.connect(self.actionGerar1)
        # Converter PWF para CTG e depois EVT
        self.actionCONV2EVT.clicked.connect(self.actionCONV2EVT1)
        # Converter PWF para CTG
        self.actionConv.triggered.connect(self.actionConv1)
        # Limpar decks de contingência
        self.actionLimpar.triggered.connect(self.actionLimparDeck1)
        # Converter resultado da análise de contingência (CA) do Anarede para Excel
        self.actionTXT_Anarede_Excel.triggered.connect(self.actionTXT_Anarede_Excel1)
    def teste(self):
        print("teste")

    def actionCONV2EVT1(self):
        anarede_dctg = easygui.fileopenbox("Selecione o arquivo DCTG_EXCA.PWF", "PWF", multiple=False)
        try:
            with open(anarede_dctg) as pd:
                ctg_anarede = pd.readlines()
            ctg_organon = []
            contador=0
            for i in ctg_anarede:
                if i[0]!='(':
                    if i[10:13]=='De:':
                        contador += 1 
                        i = str(contador) + "  '"+i[10:54]+"  ' /"
                    i = i.replace('CIRC', '\nBRANCH')
                    i = i.replace('FCAS', r'     END /   ')
                    # Falta ajustar esses espaços
                    if i[0:7]=='\nBRANCH':
                        i = [i for i in i.split(' ') if i!='']
                        deck = ''
                        deck = i[0]+'       '+i[1].zfill(5)+'        '+i[2].zfill(5)+'        '+i[3]+'  \n'
                        i=deck

                    i=i.replace('99999', '')
                    i=i.replace('FIM', ' END / ')
                    i=i.replace('DCTG', r"       15.000 /")
                    ctg_organon.append(i)      
            contador = 0
            evt_final=''
            for i in ctg_organon:
                if "  'De:" in i:
                    #Teste    
                    contador += 1
                    i0 = str(contador) + i
                    evt_final += i0
                    if i0[18:21] == '500' or i0[37:40] == '500':
                        tempo = '0.3000'
                    else:
                        tempo = '0.3500'
                        
                if i[:7]=='\nBRANCH':
                    
                    i1 = i.replace('BRANCH', '56')
                    i1 = i1[:20] + '0     0    0.0000    0.0000    0.2000 "xxxxxxxxxxxx" "xxxxxxxxxxxx"       0.000 /'
                
                    i2 = i.replace('BRANCH', '57')
                    i2 = i2[:20] + f'0     0    0.0000    0.0000    {tempo} "xxxxxxxxxxxx" "xxxxxxxxxxxx"       0.000 /'
                    
                    i3 = i.replace('BRANCH', '7')
                    i3 = i3[:37] + f'0.0000    0.0000    {tempo} "xxxxxxxxxxxx" "xxxxxxxxxxxx"       0.000 /'
                    
                    i4 = '-99 /'
                    
                    evt_final += i1  + i2 + i3 + '\n' + i4 + '\n'

            evt_final += '-999 /'  

            with open(os.path.split(anarede_dctg)[0]+'\\DCTG_EXCA_EVT.evt', 'w') as pd:
                pd.writelines(evt_final)  
        except:
            ctypes.windll.user32.MessageBoxW(0, "Erro ao tentar abrir o arquivo", "Erro", 0)

    def actionTXT_Anarede_Excel1(self):
        # Ler txt de contingência do anarede
        anarede_texto_file = easygui.fileopenbox("Selecione o arquivo de texto do resultado da análise de contingências do anarede", "txt", 
                                                filetypes=["*.txt", "*.pwf", "*.dat"],
                                                multiple=False)
        with open(anarede_texto_file) as f:
            texto_anarede = f.readlines()

        texto_resumo=''
        for i in range(0, len(texto_anarede)):
            try:
                if ' CONTINGENCIA' in texto_anarede[i] and ' X------------X------------X' in texto_anarede[i+9]:
                    texto_resumo+=texto_anarede[i]+'\n'
                    texto_resumo+=texto_anarede[i+2]+'\n'        
                x='0'
                if ' X------------X------------X' in texto_anarede[i]:
                    while ' -------------------- IND SEVER.' not in x:
                        texto_resumo+=texto_anarede[i]+'\n'
                        x=texto_anarede[i]
                        i+=1
            except:
                pass
        texto_resumo=texto_resumo.replace('\n\n', '\n')
        texto_resumo=texto_resumo.replace('\n\n\n', '\n')

        # Salva o texto resumo das contingências
        with open(os.path.split(anarede_texto_file)[0]+'\\texto_ctgs_limpo.txt', 'w') as f:
            f.write(texto_resumo)
            

        # Filtrar contingências para excel
        texto21 = texto_resumo.split('\n')
        sobr=[]
        for i in range(0, len(texto21)):
            if texto21[i][7:11].isnumeric():
                if ' CIRCUITO da Barra' in texto21[i-3]:
                    ctgs = re.findall('CIRCUITO da Barra \s*(\d*) ([a-zA-z.\-0-9]*)\s* p/ Barra \s*(\d*) ([a-zA-z.\-0-9]*)\s*Circ \s*(\d*)', texto21[i-3])
                    print(ctgs)
                    num_de, bar_de, num_para, bar_para, nc = ctgs[0]

                sobr.append((num_de, num_para, nc, bar_de, bar_para, texto21[i][6:11], texto21[i][19:24], texto21[i+1][28:30], texto21[i+1][2:14], texto21[i+1][15:27], texto21[i][71:79]))

        # Ajustar dataframe
        testefinal = pd.DataFrame(sobr)
        testefinal.columns = ['CTG_De', 'CTG_Para', 'CTG_nc', 'CTG_Bar_De', 'CTG_Bar_Para', 'OVER_De', 'OVER_Para', 'OVER_nc', 'OVER_Bar_De', 'OVER_Bar_Para', 'Percentual']

        # Salvar Pandas
        writer = pd.ExcelWriter(os.path.split(anarede_texto_file)[0]+'\\Sobrecargas_CasoBase.xlsx', engine='xlsxwriter')
        testefinal.to_excel(writer, sheet_name = 'CTG_Completo', index=False)

        # Filtrando só as sobrecargas
        testefinal['Filtro1']=testefinal['OVER_De']+testefinal['OVER_Para']+testefinal['OVER_nc']
        testefinal_resumo = testefinal.drop_duplicates(subset=['Filtro1'], keep='first')
        testefinal_resumo.drop(columns=['Filtro1'])
        testefinal_resumo.to_excel(writer, sheet_name = 'Sobrecargas_Resumo', index=False)


        # FILTRO 2 - CTG x OVERLOAD
        testefinal['Filtro2']=testefinal['CTG_De']+testefinal['CTG_Para']+testefinal['CTG_nc']
        testefinal.to_excel(writer, sheet_name = 'CTG x OVER', index=False)
        workbook = writer.book
        worksheet = writer.sheets['CTG x OVER']
        merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 2})

        # Merge cells
        i = 0
        while i < len(testefinal['Filtro2']) - 1:
            cont = 0
            inicial = i
            while testefinal['Filtro2'][i] == testefinal['Filtro2'][i+1]:
                cont += 1
                i += 1
                if i == len(testefinal['Filtro2']) - 1:
                    break
            if i != len(testefinal['Filtro2']) - 1:
                if testefinal['Filtro2'][i] != testefinal['Filtro2'][i+1]:
                    i += 1
            worksheet.merge_range(inicial+1, 0, inicial + cont+1, 0, testefinal['CTG_De'][inicial+1], merge_format)
            worksheet.merge_range(inicial+1, 1, inicial + cont+1, 1, testefinal['CTG_Para'][inicial+1], merge_format)
            worksheet.merge_range(inicial+1, 2, inicial + cont+1, 2, testefinal['CTG_nc'][inicial+1], merge_format)
            worksheet.merge_range(inicial+1, 3, inicial + cont+1, 3, testefinal['CTG_Bar_De'][inicial+1], merge_format)
            worksheet.merge_range(inicial+1, 4, inicial + cont+1, 4, testefinal['CTG_Bar_Para'][inicial+1], merge_format)
            
            
        # FILTRO 1 - OVERLOAD x CTG
        new_df = testefinal[['OVER_De', 'OVER_Para', 'OVER_nc', 'OVER_Bar_De', 'OVER_Bar_Para', 'CTG_De', 'CTG_Para', 'CTG_nc', 'CTG_Bar_De', 'CTG_Bar_Para', 'Percentual', 'Filtro1', 'Filtro2']]
        new_df.sort_values(by=['Filtro1'], inplace=True)
        new_df = new_df.reset_index(drop=True)
        new_df.to_excel(writer, sheet_name = 'OVER x CTG', index=False)
        workbook = writer.book
        worksheet = writer.sheets['OVER x CTG']
        merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 2})

        # Merge cells
        i = 0
        while i < len(new_df['Filtro1']) - 1:
            cont = 0
            inicial = i
            while new_df['Filtro1'][i] == new_df['Filtro1'][i+1]:
                cont += 1
                i += 1
                if i == len(new_df['Filtro1']) - 1:
                    break
            if i != len(new_df['Filtro1']) - 1:
                if new_df['Filtro1'][i] != new_df['Filtro1'][i+1]:
                    i += 1
            worksheet.merge_range(inicial+1, 0, inicial + cont+1, 0, new_df['OVER_De'][inicial+1], merge_format)
            worksheet.merge_range(inicial+1, 1, inicial + cont+1, 1, new_df['OVER_Para'][inicial+1], merge_format)
            worksheet.merge_range(inicial+1, 2, inicial + cont+1, 2, new_df['OVER_nc'][inicial+1], merge_format)
            worksheet.merge_range(inicial+1, 3, inicial + cont+1, 3, new_df['OVER_Bar_De'][inicial+1], merge_format)
            worksheet.merge_range(inicial+1, 4, inicial + cont+1, 4, new_df['OVER_Bar_Para'][inicial+1], merge_format)


        writer.save()

    def actionLimparDeck1(self):
        # Ler txt de contingência do anarede
        arqv_ctg = easygui.fileopenbox("Selecione DCTG_EXCA.pwf", "pwf", 
                                                filetypes=["*.txt", "*.pwf", "*.dat"],
                                                multiple=False)
        with open(arqv_ctg, 'r') as f:
            ctgs = f.readlines()
            
        for i in range(0, len(ctgs)):
            if ctgs[i][39:42] in ['UTE', 'UHE', 'EOL', 'UFV', 'CER', 'SIN'] or ctgs[i][20:23] in ['UTE', 'UHE', 'EOL', 'UFV', 'CER', 'SIN'] or ctgs[i][42:45] in ['034', '013', '069'] or ctgs[i][23:26] in ['034', '013', '069'] or (ctgs[i][42:45] in ['000'] and ctgs[i][23:26] in ['000']):
                ctgs[i] = '(' + ctgs[i]
                ctgs[i+1] = '(' + ctgs[i+1]
                ctgs[i+2] = '(' + ctgs[i+2]
                ctgs[i+3] = '(' + ctgs[i+3]

        with open(os.path.split(arqv_ctg)[0] + '\\DCTG_EXCA_edit.pwf', 'w') as f:
            f.writelines(ctgs)
    
    # Função para converter o arquivo de contingências do anarede para organon
    def actionConv1(self):
        anarede_dctg = easygui.fileopenbox("Selecione o arquivo DCTG_EXCA.PWF", "PWF", multiple=False)
        try:
            with open(anarede_dctg) as pd:
                ctg_anarede = pd.readlines()

            ctg_organon = []
            for i in ctg_anarede:
                if i[0]!='(':
                    if i[10:13]=='De:':
                        i = "  '"+i[10:54]+"  '"
                    i = i.replace('CIRC', '\nBRANCH')
                    i = i.replace('FCAS', r'     END /   ')
                    # Falta ajustar esses espaços
                    if i[0:7]=='\nBRANCH':
                        i = [i for i in i.split(' ') if i!='']
                        deck = ''
                        deck = i[0]+'       '+i[1].zfill(5)+'        '+i[2].zfill(5)+'        '+i[3]+'  \n'
                        i=deck

                    i=i.replace('99999', '')
                    i=i.replace('FIM', ' END / ')
                    i=i.replace('DCTG', "' Lista de contingências Organon '")
                    ctg_organon.append(i)
            with open(os.path.split(anarede_dctg)[0]+'\\DCTG_EXCA_CTG.ctg', 'w') as pd:
                pd.writelines(ctg_organon)
                
            # Conclusão
            QMessageBox.about(self, "PWF para CTG Finalizado", "Deck CTG convertido na pasta!")
        except:
            ctypes.windll.user32.MessageBoxW(0, "Erro ao tentar abrir o arquivo", "Erro", 0)

       
    # Carrega a fotólica e retorna o código das usinas conectadas àquela subestação (DGMT)
    # Preenche as labels com o endereço da planilha da base de dados da fotólica e a subestação conectada
    def abrirFotolica1(self):
        # Abre fotólica
        # Base da Fotolica
        bd_fotolica = easygui.fileopenbox("Selecione a base da fotolica", "xlsx", multiple=False)

        # Dataframe
        data_fotolica = pd.read_excel(bd_fotolica)

        # Filtrar NNE e gerações válidas
        data_NNE = data_fotolica[(data_fotolica['Subsistema']=='N/NE') & (data_fotolica['Tipo da Rede de Conexão']!='Dist') & (data_fotolica['Situação']!='Outorga revogada') & (data_fotolica['Situação']!='Parecer de Acesso Expirado') & (data_fotolica['Status']==True)].copy()
        pontos_conexao = list(set(data_NNE['Ponto de Conexão']))
        pontos_conexao.sort()

        # Escolher Ponto de Conexão  
        text = "Selecione a subestação"

        # window title
        title = "Gerações no Ponto de Conexão"

        # item choices
        choices = pontos_conexao

        # creating a button box
        output = easygui.choicebox(text, title, choices)

        # Filtrar barras
        barras_ponto_conexao = data_NNE[data_NNE['Ponto de Conexão']==output]

        # Agrupar por número de barra e somar os campos de potência instalada e reativo
        barras_NNE = barras_ponto_conexao.groupby(['Nº da Barra_ANAREDE']).sum()
        barras_NNE_filtrada = barras_NNE[['Potência Instalada (MW)', 'Reativo Mín. Total (Mvar)', 'Reativo Max. Total (Mvar)']]

        # Ajustar dataframe para criar o deck
        barras_NNE_filtrada = barras_NNE_filtrada.reset_index()
        barras_NNE_filtrada['Nº da Barra_ANAREDE'] = barras_NNE_filtrada['Nº da Barra_ANAREDE'].astype(str)
        barras_NNE_filtrada['Reativo Mín. Total (Mvar)'] = barras_NNE_filtrada['Reativo Mín. Total (Mvar)'].round(2)
        barras_NNE_filtrada['Reativo Max. Total (Mvar)'] = barras_NNE_filtrada['Reativo Max. Total (Mvar)'].round(2)
        barras_NNE_filtrada['Potência Instalada (MW)'] = barras_NNE_filtrada['Potência Instalada (MW)'].round(2)

        # Criar deck
        deck_DGMT = """DGMT
(SE) (Bger (Pmx ) (P) (Qmn) (Qmx)
"""
        for i in barras_NNE_filtrada.values.tolist():
            if len(str(i[1]))>5:
                i[1]=round(i[1], 1)
            if len(str(i[2]))>5 and str(i[2])[0]=='-':
                i[2]=int(round(i[2]))
            if len(str(i[2]))>5:
                i[2]=round(i[2], 1)
            if len(str(i[3]))>5:
                i[3]=round(i[3], 1)
            linha = ' 001 '+str(i[0]).zfill(5)+' '+str(i[1]).zfill(6)+' 100 '+str(i[2]).zfill(5)+' '+str(i[3]).zfill(5)
            deck_DGMT += linha+'\n'
        deck_DGMT += '99999'
        
        # Preencher endereço e subestação escolhida
        self.lineEdit.setText(bd_fotolica)
        self.lineEdit_2.setText(output)
        
        self.deck_DGMT = deck_DGMT
        return deck_DGMT
    
    # Abre o caso do anarede
    def actionAnarede1(self):
        # Abre caso
        openfiles = easygui.fileopenbox("Selecione o caso", "PWF/DAT", 
                                        filetypes=["*.pwf", "*.dat"],
                                        multiple=False)
        self.lineEdit_5.setText(openfiles)
    
    def actionGerar1(self):
        # ** Configurações iniciais **
        # barras candidatas
        bar_candidata = [i.strip() for i in self.lineEdit_3.text().split(',')]
        NUMERO_NIVEIS = int(self.lineEdit_4.text())
        LT_excluir_monit = [i.strip() for i in self.lineEdit_7.text().split(',')]
        BAR_excluir_monit = []
        sincronos_fic = [i.strip() for i in self.lineEdit_6.text().split(',')]
        num_caso = '2'
        
        # Leitura do caso
        with open(self.lineEdit_5.text()) as f:
            arqv_pwf = f.readlines()
        
        # Criar pasta Anarede e Organon
        if not os.path.exists('Anarede_Margem'):
            os.makedirs('Anarede_Margem')
        if not os.path.exists('Organon_Margem'):
            os.makedirs('Organon_Margem')
        if not os.path.exists('Organon_CaseManager'):
            os.makedirs('Organon_CaseManager')
        
        BARRAS = bar_candidata[:]
        def extrai_barras(arqv_pwf, BARRAS):
            # Posições do DLIN
            linha_inicial_dlin = arqv_pwf.index('DLIN\n')
            linha_final_dlin = arqv_pwf.index('99999\n', linha_inicial_dlin)

            # Procura e Extrai DLIN
            DLIN = []
            for i in range(linha_inicial_dlin, linha_final_dlin):
                if arqv_pwf[i][0:5].strip() in BARRAS or arqv_pwf[i][10:15].strip() in BARRAS or arqv_pwf[i][58:64].strip().replace('-','').replace('+','') in BARRAS:
                    DLIN.append(arqv_pwf[i][:5].strip())
                    DLIN.append(arqv_pwf[i][10:15].strip())
                    DLIN = list(set(DLIN))
            return DLIN

        # Níveis de vizinhança - recomendado = 2 (adjacente e adjacente do adjacente)
        i = 0
        while i < NUMERO_NIVEIS:
            BARRAS = extrai_barras(arqv_pwf, BARRAS)
            i += 1

        # Áreas das barras da vizinhança escolhida
        linha_inicial_dbar = arqv_pwf.index('DBAR\n')
        linha_final_dbar = arqv_pwf.index('99999\n', linha_inicial_dbar)
        DBAR = []
        BAR_NOME = []
        lista_areas = []
        tensaoBarra = []
        for i in range(linha_inicial_dbar+2, linha_final_dbar):
            if arqv_pwf[i][0:5].strip() in BARRAS:
                DBAR.append(arqv_pwf[i])
                BAR_NOME.append((arqv_pwf[i][0:5].strip(), arqv_pwf[i][10:22].strip()))
                tensaoBarra.append((arqv_pwf[i][0:5].strip(), arqv_pwf[i][9:10].strip()))
                lista_areas.append(arqv_pwf[i][73:76])
                
        # Excluir barras indesejadas para monitoração
        barras_exclusao=[]
        areas_filtradas=list(set(lista_areas))
        for linha in arqv_pwf:
            if (linha[73:76] in areas_filtradas and linha[16:19] in ['UTE', 'UHE', 'UFV', 'EOL', 'CER', 'PCH'])  or (linha[73:76] in areas_filtradas and linha[19:22] in ['034']):
                barras_exclusao.append(linha[0:5].zfill(5))
                #print(linha)

        # Gerador do deck Gera_CTG
        deck_ctg="""(**********************************************************************************************
(*** Gerador de lista de contingências pelo Código de Execução EXCA                         ***
(*** ---------------------------------------------------------------                        ***
(**********************************************************************************************
DBAR
(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10"""
        for bar in BARRAS:
            deck_ctg += '\n' + "{:05d}".format(int(bar)) + 'm'+'                                                                   888'
        deck_ctg += '\n99999\nexlf iang\nEXCA GRAV 80CO FILE\nAREA   888\n99999\n'
        areas_listadas = list(set(lista_areas))
        areas_listadas.sort()
        deck_ctg += '(areas: ' + str(areas_listadas) + '\nFIM'
        with open('Anarede_Margem\\GeraLista DCTG_EXCA.pwf', 'w') as f:
            f.write(deck_ctg)

        # ------------- DECK MARGEM ---------------------------------
        # Por enquanto, só suporta uma única subestação

        deck_margem="""( 
( CONFIGURAÇÕES INICIAIS
( ------------------------------------------------------------------------
( ** Desliga Tensão em Barra Remota - CREM ** )
DOPC
(Op) E (Op) E (Op) E (Op) E (Op) E (Op) E (Op) E (Op) E (Op) E (Op) E
CREM D CTAP D
99999
( Barras com síncronos fictícios
DBAR
(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10
"""

        # Síncronos fictícios
        if len(sincronos_fic)> 0 and '' not in sincronos_fic:
            for i in sincronos_fic:
                deck_margem += i.zfill(5) + 'M 1                1000              -99999999\n' 
            deck_margem += '99999\n'
        else:
            deck_margem += '99999\n'

        # Apagar dados de monitoração anteriores
        deck_margem += """( ** Ajusta DMTE e DMFL para área de interesse **)
DMTE
(tp) (no ) C (tp) (no ) C (tp) (no ) C (tp) (no ) O F
AREA     1 A AREA   883                           E
99999
DMFL
(tp) (no ) C (tp) (no ) C (tp) (no ) C (tp) (no ) O F
AREA     1 A AREA   883                           E
99999
DMTE
"""

        # Áreas a serem monitoradas
        for area in areas_listadas:
            deck_margem += 'AREA   '+area+'                                        A\n'
        deck_margem += '99999\nDMFL\n'
        for area in areas_listadas:
            deck_margem += 'AREA   '+area+'                                        A\n'
        deck_margem += '99999\n'

        # Constantes de tolerância
        deck_margem += """(
(Constantes de Tolerância de Fluxo e de Tensão
(******************************************************************
DCTE
(Mn) ( Val) (Mn) ( Val) (Mn) ( Val) (Mn) ( Val) (Mn) ( Val) (Mn) ( Val)
TLMF    1.0
TLMT    5.0
99999
"""
        # Excluir barras no DMFL
        deck_margem += '(** Excluir Barras de Usinas e CER **)\n'
        deck_margem += 'DMFL\n'
        for i in barras_exclusao:
            deck_margem +='barr '+i+'                                        E\n'
        deck_margem += '99999\n' 
        
        # Barras ou LTs a serem excluidos da monitoração
        if len(LT_excluir_monit)> 0 and '' not in LT_excluir_monit:
            deck_margem += '(** Excluir Determinadas LTs Monitoração **)\n'
            deck_margem += 'DMFL CIRC\n'
            for i in LT_excluir_monit:
                de_bar = re.findall('(\d*)-(\d*)-(\d*)|$', i)[0][0]
                para_bar = re.findall('(\d*)-(\d*)-(\d*)|$', i)[0][1]
                nc_bar = re.findall('(\d*)-(\d*)-(\d*)|$', i)[0][2]
                deck_margem += de_bar.zfill(5)+' '+para_bar.zfill(5)+' '+nc_bar.zfill(2)+'                                                             E\n'
            deck_margem += '99999\n' 
        if len(BAR_excluir_monit) > 0 and '' not in BAR_excluir_monit:
            deck_margem += '(** Excluir Determinadas Barras Monitoração **)\n'
            deck_margem += 'DMTE\n'
            for i in BAR_excluir_monit:
                deck_margem += 'barr'+' '+i.zfill(5)+'                                        E\n'
            deck_margem += '99999\nexlf\nRELA RMON MOST MOSF\n' 
        
        # Carrega deck das contingências
        deck_margem += """(** Deck das contingências **)
ulog
1
DCTG_EXCA_edit.PWF
"""

        # Alteração para barras candidatas para PV
        deck_margem += """( CÁLCULO DA MARGEM POR BARRAMENTO
( ------------------------------------------------------------------------- 
(Alteração dos barramentos candidatos para tipo PV
(******************************************************************
DBAR
"""
        for i in bar_candidata:
            deck_margem += i.zfill(5)+'m 1\n'
        deck_margem+='99999\nexlf\n'

        # Dados Barramentos candidatos
        deck_margem+="""(
(Dados de Barramentos Candidatos
(******************************************************************
DEMT
(BCan (   Iden   ) (SE) (SA) (Ar) (P.CC) (Pmx ) (Pb (Ps O   
"""
        for bar in bar_candidata:
            for barra, bar_nome in BAR_NOME:
                if barra == bar:
                    deck_margem+=bar.zfill(5)+' '+bar_nome+' '+'1'.zfill(3)+'\n'
        deck_margem+='99999\n'

        # Dados de Gerações das subestações
        deck_margem+=f"""(
(Dados de Gerações das Subestações
(******************************************************************
{self.deck_DGMT}
(
(Cálculo de Margens: dados do DCTG e passos padrões (opção JUMP)
(******************************************************************
( Se quiser uma etapa pré-processamento para avaliar contingências:
(EXMT EMRG MFCT ICMB TAPC VLDC ROUT 
( ICMB - Mostra apenas a margem limitante, se tirar, mostra normal/emergencia
EXMT EMRG MFCT ICMB TAPC ETP1 ROUT 
((tp) (num) C (tp) (num) C (tp) (num) C (tp) (num) O (Passo (Pasmn             
(                                                      100    20
99999
FIM"""
        # Criar deck margem_barramento
        with open('Anarede_Margem\\margem_barramento.pwf', 'w') as f:
            f.write(deck_margem)
            
        # ORGANON 
        # Arquivo SPT - Organon
        deck_spt = deck_margem.split('\n')
        inicio_spt = deck_margem.split('\n').index('DEMT')
        fim_spt = deck_margem.split('\n').index('(Cálculo de Margens: dados do DCTG e passos padrões (opção JUMP)')
        deck_spt = deck_spt[inicio_spt:fim_spt]
        deck_spt.insert(0, 'exlf')
        deck_spt = '\n'.join(deck_spt)
        deck_spt += """( Adiciona outra barra de referência
(DWMT
((SE) (Bger (Pmx ) (Pb (Qmn) (Qmx) (Ps
(  1   6369
(99999
marginb3 mwmax=3600. mwstep=25. mwtol=5. vviotol=1.0 pfctg=t reset=f
end"""
        with open('Organon_Margem\\margem.spt', 'w') as f:
            f.write(deck_spt)
            
        # Arquivo WFS - Organon
        deck_wfs = """configuracoes.prm
{0}
DCTG_EXCA_CTG.ctg
margem.def
margem.spt""".format(self.lineEdit_5.text().split('\\')[-1])
        with open('Organon_Margem\\margem.wfs', 'w') as f:
            f.write(deck_wfs)
            
        # Case Manager - Organon
        monitor_organon=' MONITOR\n'
        for area in areas_listadas:
            monitor_organon += ' AREA     '+area.zfill(3)+'     '+'230.0   500. BOTH\n'
        monitor_organon+='END /'
        with open('Organon_CaseManager\\monitor_organon.def', 'w') as f:
            f.write(monitor_organon)
            
        # Copiar arquivos - PWF, PRM, DEF
        shutil.copy(self.lineEdit_5.text(), 'Organon_Margem')
        shutil.copy(self.lineEdit_5.text(), 'Anarede_Margem')
        shutil.copy(self.lineEdit_5.text(), 'Organon_CaseManager')
        shutil.copy('Adicionais\\configuracoes.prm', 'Organon_Margem')
        shutil.copy('Adicionais\\margem.def', 'Organon_Margem')
        shutil.copy('Adicionais\\BNT1.dat', 'Organon_CaseManager')
        shutil.copy('Adicionais\\Organon.prm', 'Organon_CaseManager')
        shutil.copy('Adicionais\\Instrucoes.txt', 'Organon_CaseManager')          

        
        # Conclusão
        QMessageBox.about(self, "Decks Finalizados", "Decks Concluídos!")


def main():
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
#    app = QApplication(sys.argv)
        form = MarginApp()
        form.show()
        app.exec_()

if __name__ == '__main__':
    main()