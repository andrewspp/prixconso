from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import csv
import os
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Thread-local storage pour rendre les logs thread-safe
thread_local = threading.local()

# --- Configuration CSV ---
CSV_FILENAME = 'carrefour_product_data.csv'
CSV_HEADERS = ['PostalCode', 'StoreName', 'PricePerUnit', 'ProductName', 'ProductURL']

# Verrou pour l'écriture dans le fichier CSV
csv_lock = threading.Lock()

# --- Listes des produits et codes postaux à traiter ---
PRODUITS = [
    "https://www.carrefour.fr/p/jambon-sel-reduit-conservation-sans-nitrite-le-bon-paris-herta-3154230810131",
    "https://www.carrefour.fr/p/oeufs-bio-calibre-moyen-sans-antibiotique-sans-ogm-loue-3251320021030",
    "https://www.carrefour.fr/p/fromage-camembert-president-3228021170039",
    "https://www.carrefour.fr/p/yaourt-nature-carrefour-classic-3270190021438", 
    "https://www.carrefour.fr/p/filet-de-poulet-blanc-le-gaulois-3266980123994",        
    "https://www.carrefour.fr/p/carottes-vrac-3276552611057",   
    "https://www.carrefour.fr/p/pommes-pink-lady-vrac-3000000035542",   
    "https://www.carrefour.fr/p/lait-demi-ecreme-de-nos-campagnes-carrefour-classic-3560071080914", 
    "https://www.carrefour.fr/p/bananes-cavendish-vrac-3000000033272",
    "https://www.carrefour.fr/p/beurre-gastronomique-doux-carrefour-classic-3270190020288",
    "https://www.carrefour.fr/p/saumon-fume-atlantique-labeyrie-3033610069430",
    "https://www.carrefour.fr/p/tomates-rondes-en-grappe-vrac-3276552413026",
    "https://www.carrefour.fr/p/mandarines-vrac-3000000033098",
    "https://www.carrefour.fr/p/pommes-bicolores-bio-3276550311843",
    "https://www.carrefour.fr/p/poireaux-vrac-3000000026649",

    "https://www.carrefour.fr/p/pates-spaghetti-n05-barilla-8076800105056", 
    "https://www.carrefour.fr/p/riz-basmati-carrefour-extra-3560070837984",
    "https://www.carrefour.fr/p/pate-a-tartiner-aux-noisettes-et-au-cacao-nutella-3017620429484",
    "https://www.carrefour.fr/p/cafe-capsules-delizioso-intensite-5-compatibles-nespresso-l-or-8711000360477",
    "https://www.carrefour.fr/p/cereales-miel-pops-kellogg-s-5059319023762",
    "https://www.carrefour.fr/p/sauce-tomato-ketchup-heinz-0000087157215",
    "https://www.carrefour.fr/p/moutarde-fine-de-dijon-l-originale-maille-8720182556738",
    "https://www.carrefour.fr/p/huile-d-olive-vierge-extra-puget-3178050000725",
    "https://www.carrefour.fr/p/farine-de-ble-fluide-t45-carrefour-classic-3270190117315",
    "https://www.carrefour.fr/p/sucre-en-poudre-carrefour-classic-3560071410964",
    "https://www.carrefour.fr/p/cerneaux-de-noix-carrefour-original-3560071462949",
    "https://www.carrefour.fr/p/pruneaux-d-agen-denoyautes-reflets-de-france-3560070439942",
    "https://www.carrefour.fr/p/dattes-deglet-nour-la-favorite-3068233500404",
    "https://www.carrefour.fr/p/olives-vertes-vertes-en-rondelles-carrefour-classic-3560070317769",

    "https://www.carrefour.fr/p/soda-gout-original-coca-cola-5000112611861",
    "https://www.carrefour.fr/p/eau-de-source-plate-cristaline-3274080001005",
    "https://www.carrefour.fr/p/jus-d-orange-100-avec-pulpe-carrefour-extra-3270190023975",
    "https://www.carrefour.fr/p/jus-multifruits-myrtille-cassis-pomme-et-cranberry-innocent-5038862139137",

    "https://www.carrefour.fr/p/vin-rouge-a-o-p-medoc-la-cave-d-augustin-florent-3245414562707",
    "https://www.carrefour.fr/p/dentifrice-protection-caries-signal-3014230002076",
    "https://www.carrefour.fr/p/shampoing-amande-douche-dop-3600551142128",
    "https://www.carrefour.fr/p/papier-toilette-confort-blanc-lotus-3133200094887",
    "https://www.carrefour.fr/p/creme-de-douche-surgras-karite-cadum-3600551054469",
    "https://www.carrefour.fr/p/bain-de-bouche-integral-8-complet-signal-8720181086267",
    "https://www.carrefour.fr/p/preservatifs-nude-taille-large-fins-lubrifies-sensations-peau-contre-peau-durex-3059948002918",
    "https://www.carrefour.fr/p/creme-hydratante-nourrissante-visage-corps-mains-nivea-4005808925124",

    "https://www.carrefour.fr/p/laque-tenue-forte-schwarzkopf-3178041360098",
    "https://www.carrefour.fr/p/pizza-chorizo-carrefour-original-3560070345397",
    "https://www.carrefour.fr/p/haricots-verts-extra-fins-carrefour-classic-3270190020660",
    "https://www.carrefour.fr/p/glace-batonnet-chocolat-blanc-magnum-8711327606081",
    "https://www.carrefour.fr/p/frites-carrefour-classic-3560070057597",

    "https://www.carrefour.fr/p/croquettes-pour-chat-sterilise-au-saumon-purina-one-7613032759155",
    "https://www.carrefour.fr/p/stylo-a-bille-bic-4-colours-original-x2-shine-x2-pointe-moyenne-bic-3086123464629"
]

CODES_POSTAUX = ['01000', '01100', '01110', '01150', '01170', '01190', '01200', '01300', '01340', '01350', '01390', '01400', '01460', '01500', '01510', '01540', '01600', '01700', '01800', '01960', '02000', '02100', '02120', '02140',
                  '02170', '02190', '02200', '02220', '02230', '02250', '02260', '02270', '02300', '02320', '02340', '02370', '02400', '02450', '02460', '02600', '02880', '03000', '03100', '03120', '03150', '03160', '03190', '03270', '03300',
                    '03350', '03390', '03400', '03430', '03500', '03600', '03630', '03800', '04000', '04220', '04300', '04400', '04700', '05100', '05120', '05160', '05400', '05500', '06000', '06100', '06130', '06140', '06150', '06160', '06190',
                      '06200', '06210', '06240', '06250', '06260', '06270', '06300', '06400', '06450', '06500', '06530', '06560', '06600', '06610', '06650', '06700', '06730', '07110', '07140', '07200', '07220', '07260', '07300', '07400', 
                      '07430', '07800', '08000', '08110', '08150', '08170', '08230', '08300', '08360', '08400', '08700', '09000', '09110', '09120', '09200', '09210', '09300', '09350', '10000', '10100', '10120', '10200', '10260', '10270', 
                      '10300', '10400', '10600', '10800', '11000', '11100', '11130', '11150', '11200', '11210', '11290', '11310', '11370', '11500', '11590', '12100', '12120', '12160', '12170', '12200', '12260', '12300', '12500', '12510',
                        '12600', '13001', '13002', '13003', '13004', '13005', '13006', '13007', '13008', '13009', '13010', '13011', '13012', '13013', '13014', '13016', '13100', '13110', '13120', '13124', '13127', '13130', '13140', '13160',
                          '13180', '13220', '13290', '13300', '13340', '13400', '13410', '13500', '13530', '13600', '13730', '13770', '13780', '13920', '14000', '14100', '14120', '14123', '14150', '14160', '14200', '14230', '14270', '14290',
                            '14310', '14320', '14380', '14390', '14400', '14470', '14500', '14640', '14680', '14700', '14760', '14780', '14790', '14800', '14810', '14860', '15000', '15100', '15130', '15200', '15250', '15400', '15500', '16000',
                              '16120', '16800', '17000', '17100', '17138', '17170', '17190', '17240', '17250', '17440', '17570', '17580', '17630', '17670', '17690', '17740', '17770', '17880', '17940', '18000', '18100', '18110', '18200', '18220',
                                '18300', '18390', '18400', '18500', '18570', '18700', '19100', '19110', '19130', '19190', '19350', '20000', '20110', '20167', '20290', '20600', '21000', '21190', '21200', '21300', '21320', '21700', '21800', 
                                '22000', '22100', '22150', '22170', '22200', '22360', '22400', '22420', '22500', '22580', '22630', '22680', '22700', '22960', '23000', '23200', '23210', '23230', '23300', '23400', '23600', '24100', '24130', 
                                '24170', '24200', '24220', '24240', '24270', '24310', '24340', '24410', '24450', '24500', '25000', '25200', '25220', '25320', '25400', '25420', '25460', '25480', '25500', '25770', '26000', '26200', '26300', '26540', '26700', '27000', '27120', '27130', '27140', '27150', '27160', '27170', '27190', '27200', '27210', '27220', '27230', '27240', '27260', '27300', '27310', '27320', '27350', '27380', '27400', '27500', 
                                '27700', '27800', '27930', '28000', '28130', '28150', '28170', '28210', '28260', '28300', '28800', '29000', '29120', '29160', '29170', '29200', '29280', '29290', '29300', '29340', '29500', '29600', '29750', '29760', '29780', '29880', '29950', '30000', '30100', '30127', '30130', '30133', '30160', '30200', '30210', '30250', '30300', '30340', '30400', '30500', '30510', '30600', '30700', '31000', '31100', '31120', '31140', '31150', '31170', '31180', '31190', '31200', '31210', '31220', '31240', '31250', '31270', '31300', '31310', '31370', '31380', '31390', '31400', '31410', '31430', '31460', '31470', '31480', '31500', 
                                '31560', '31570', '31600', '31670', '31700', '31750', '31770', '31790', '31800', '31820', '31840', '32000', '32100', '32110', '32190', '32200', '32300', '32500', '32600', '33000', '33100', '33110', '33120', '33130', '33138', '33140', '33170', '33200', '33210', '33250', '33300', '33310', '33320', '33340', '33360', '33370', '33450', '33470', '33500', '33600', '33640', '33670', '33700', '33710', '33720', '33750', '33770', '33780', '33980', '33990', '34000', '34070', '34090', '34140', '34160', '34170', '34200', '34230', '34250', '34340', '34350', '34370', '34410', '34420', '34430', '34540', '34560', '34660', '34920', '34970', '34980', '35000', '35120', '35131', '35136', '35140', '35200', '35235', '35300', '35310', '35400', '35430', '35510', '35540', '35700', '35760', '35800', '35830', '35850', '35890', '36000', '36100', 
                                '36130', '36150', '36200', '36260', '36400', '36500', '36800', '37000', '37100', '37110', '37130', '37150', '37190', '37200', '37700', '38000', '38070', '38080', '38120', '38130', '38140', '38150', '38160', '38190', '38200', '38230', '38240', '38260', '38270', '38300', '38330', '38360', '38390', '38400', '38410', '38430', '38460', '38490', '38500', '38520', '38580', '38640', '38750', '38780', '38890', '39000', '39130', '39570', '40000', '40100', '40120', '40130', '40160', '40190', '40200', '40220', '40240', '40270', '40300', '40360', '40400', '40500', '40550', '40700', '40800', '40990', '41000', '41100', '41200',
                                  '41260', '41300', '41400', '41600', '42000', '42100', '42110', '42120', '42150', '42153', '42210', '42220', '42240', '42290', '42300', '42340', '42410', '42420', '42500', '42510', '42540', '42600', '42800', '43000', '43100', '43120', '43190', '43240', '43320', '43600', '43750', '44000', '44100', '44110', '44119', '44300', '44350', '44380', '44400', '44420', '44450', '44600', '44630', '44700', '44760', '44800', '44980', '45000', '45100', '45120', '45140', '45200', '45210', '45240', '45250', '45300', '45330', '45370', '45500', '45770', '45800', '46000', '46100', '46110', '46220', '46300', '46800', '47000', '47200', 
                                  '47390', '48300', '48400', '49000', '49100', '49110', '49124', '49240', '49270', '49300', '49400', '49460', '49570', '49630', '50000', '50100', '50140', '50160', '50170', '50190', '50200', '50220', '50250', '50270', '50300', '50330', '50400', '50500', '50550', '50560', '50570', '50590', '50600', '50700', '50710', '51000', '51100', '51110', '51120', '51130', '51170', '51200', '51210', '51230', '51420', '51430', '51500', '51700', '52400', '53000', '53500', '54000', '54135', '54360', '54380', '54530', '54540', '54590', '54700', '54840', '55130', '55160', '55500', '56000', '56100', '56130', '56150', '56190', '56230', '56240', '56270', '56370', '56380', '56390', '56400', '56410', '56450', '56470', '56500', '56520', '56550', '56600', '56850', '56860', '56870', '56890', '57000', '57100', '57160', '57190', '57365', '57390', 
                                  '57480', '57500', '57600', '57660', '57970', '58000', '58180', '58200', '58300', '58320', '58700', '59000', '59100', '59110', '59111', '59112', '59113', '59114', '59120', '59122', '59123', '59124', '59128', '59129', '59133', '59139', '59141', '59148', '59151', '59152', '59155', '59158', '59160', '59163', '59167', '59170', '59177', '59180', '59190', '59193', '59200', '59210', '59211', '59215', '59216', '59220', '59221', '59229', '59230', '59233', '59239', '59240', '59260', '59265', '59279', '59280', '59286', '59287', '59290', '59300', '59330', '59400', '59410', '59430', '59440', '59450', '59460', '59490', '59495', '59500', '59510', '59550', '59554', '59560', '59570', '59600', '59610', '59630', '59650', '59680', '59770', '59780', '59800', '59910', '59920', '59940', '60000', '60100', '60120', '60150', '60200', '60210', '60260', '60280', '60300', '60320', '60340', '60360', '60390', '60420', '60490', '60500', '60530', '60700', '60800', '61000', '61100', '61120', '61130', '61200', '61250', '61260', '61500', '61600', '61700', 
                                  '61800', '62000', '62100', '62116', '62119', '62120', '62126', '62129', '62138', '62140', '62147', '62152', '62160', '62164', '62170', '62180', '62190', '62200', '62210', '62215', '62217', '62231', '62232', '62240', '62250', '62260', '62270', '62280', '62300', '62310', '62320', '62330', '62340', '62360', '62370', '62400', '62410', '62450', '62460', '62500', '62510', '62520', '62550', '62560', '62580', '62600', '62610', '62620', '62630', '62650', '62660', '62690', '62720', '62770', '62790', '62800', '62810', '62840', '62910', '62940', '62990', '63000', '63100', '63110', '63190', '63200', '63210', '63230', '63260', '63300', '63360', '63370', '63500', '63600', '63650', '63700', '63960', '64000', '64100', '64120', '64130', '64150', '64200', '64220', '64230', '64240', '64250', '64260', '64270', '64370', '64400', '64410', 
                                  '64500', '64600', '64700', '64990', '65000', '65100', '65110', '65170', '65190', '65200', '65300', '65310', '65370', '65400', '66000', '66120', '66190', '66270', '66310', '66400', '66530', '66600', '66740', '66750', '66760', '67000', '67170', '67190', '67290', '67630', '67800', '67960', '68100', '68110', '68300', '68460', '68600', '68840', '69002', '69003', '69004', '69006', '69007', '69008', '69009', '69100', '69120', '69130', '69140', '69160', '69190', '69200', '69210', '69220', '69270', '69330', '69340', '69400', '69420', '69460', '69480', '69530', '69540', '69550', '69590', '69600', '69620', '69680', '69700', 
                                  '69720', '69740', '69800', '70100', '70160', '70250', '70360', '70500', '70800', '71100', '71170', '71200', '71250', '71310', '71380', '71500', '71600', '71680', '71700', '71850', '71880', '72000', '72100', '72120', '72130', '72160', '72200', '72230', '72300', '72320', '72330', '72400', '72460', '72470', '73000', '73100', '73110', '73140', '73170', '73200', '73220', '73440', '73480', '73550', '73620', '73630', '73700', '74000', '74100', '74110', '74120', '74130', '74160', '74200', '74270', '74300', '74310', '74370', '74430', '74700', '74930', '74950', '75001', '75003', '75004', '75005', '75006', '75007', '75008', '75009', '75010', '75011', '75012', '75013', '75014', '75015', '75016', '75017', '75018', '75019', '75020', '76000', '76110', '76130', '76133', '76140', '76200', '76210', '76230', '76240', '76250', '76280', '76300', '76310', '76320', '76330', '76360', '76370', '76400', '76410', '76420', '76430', '76440', '76450', '76480', '76490', '76500', '76550', '76560', '76570', '76580', '76600', '76620', '76680', '76730', 
                                  '76750', '76850', '76910', '77000', '77090', '77100', '77120', '77124', '77127', '77130', '77140', '77150', '77165', '77190', '77210', '77220', '77230', '77250', '77300', '77340', '77350', '77360', '77370', '77380', '77390', '77410', '77420', '77440', '77470', '77480', '77500', '77510', '77540', '77570', '77590', '77600', '77700', '77950', '78000', '78100', '78120', '78140', '78160', '78180', '78200', '78240', '78280', '78290', '78300', '78330', '78360', '78410', '78430', '78440', '78450', '78470', '78500', '78520', '78540', '78550', '78600', '78630', '78640', '78700', '78711', '78840', '78860', '78960', '78970', '78990', '79000', '79150', '79180', '79260', '79300', '80000', '80090', '80100', '80110', '80120', '80150', '80160', '80190', '80200', '80210', '80230', '80260', '80270', '80290', '80310', '80400', '80430', '80460', '80480', '80700', '81000', '81100', '81150', '81160', '81200', '81230', '81250', '81310', '81370', '81700', '81800', '82000', '82140', '82170', '82290', '82300', '82410', '82600', '83000', '83120', 
                                  '83130', '83140', '83150', '83160', '83190', '83200', '83240', '83260', '83300', '83310', '83330', '83390', '83400', '83440', '83480', '83490', '83520', '83560', '83720', '83790', '83910', '83980', '84000', '84100', '84120', '84200', '84270', '84320', '84430', '84550', '84700', '84810', '85000', '85100', '85170', '85260', '86000', '86220', '86300', '86380', '86800', '87000', '87220', '87300', '87400', '87570', '87800', '88000', '88230', '88500', '88560', '89000', '89100', '89140', '89144', '89190', '90000', '91000', '91100', '91120', '91150', '91160', '91190', '91200', '91300', '91360', '91380', '91420', '91450', '91470', '91490', '91590', '91610', '91620', '91630', '91650', '91700', '91800', '91940', '92000', '92100', '92130', '92140', '92150', '92200', '92210', '92230', '92260', '92270', '92290', '92310', '92320', '92340', '92350', '92360', '92380', '92390', '92400', '92500', '92600', '92700', '93100', '93150', '93160', '93190', '93240', '93250', '93270', '93290', '93310', '93340', '93400', '93460', '93700', '94000', '94100', '94130', '94140', '94160', '94200', '94205', '94210', '94230', '94240', '94260', '94300', '94350', '94400', '94410', '94440', '94490', '94500', '94520', '94800', '95110', '95120', '95150', '95170', '95180', '95190', '95220', '95270', '95280', '95290', '95350', '95370', '95420', '95620', '95640', '95650', '95870', '98000']

def write_to_csv(data_row):
    """Fonction pour écrire une ligne de données dans le fichier CSV de manière thread-safe."""
    with csv_lock:
        file_exists = os.path.isfile(CSV_FILENAME)
        try:
            with open(CSV_FILENAME, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                if not file_exists or os.path.getsize(CSV_FILENAME) == 0:  # Vérifie aussi si le fichier est vide
                    writer.writerow(CSV_HEADERS)
                writer.writerow(data_row)
            logging.info(f"Données écrites dans {CSV_FILENAME}: {data_row}")
        except Exception as e:
            logging.error(f"Erreur lors de l'écriture dans le fichier CSV: {e}")

def visiter_produit_et_choisir_drive(task):
    """Fonction qui visite un produit et récupère le prix pour un code postal donné."""
    product_url, postal_code_to_search = task
    driver = None
    store_name = "N/A"
    price_per_unit = "N/A"
    product_name = "N/A"

    try:
        # --- Setup Chrome ---
        options = Options()
        options.add_argument("--start-maximized")
        # Mode headless désactivé pour voir les navigateurs
        options.add_argument('--log-level=3')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        logging.info(f"Configuration du WebDriver Chrome pour {postal_code_to_search} - {product_url}")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 25)
        short_wait = WebDriverWait(driver, 10)
        logging.info(f"Navigation vers la page produit: {product_url}")
        driver.get(product_url)

        # --- 1. Gérer les Cookies ---
        logging.info("Attente et gestion de la bannière de cookies...")
        try:
            cookies_button = wait.until(EC.element_to_be_clickable(
                (By.ID, "onetrust-accept-btn-handler")))
            driver.execute_script("arguments[0].click();", cookies_button)
            logging.info("Bouton de cookies cliqué via JS.")
            time.sleep(0.5)
        except TimeoutException:
            logging.warning("Bouton de cookies non trouvé ou pas cliquable.")
        except Exception as e:
            logging.error(f"Erreur cookies: {e}")

        # --- Extraire le nom du produit initial ---
        try:
            product_title_xpath = "//h1[contains(@class, 'product-title')]"
            product_title_element = wait.until(EC.presence_of_element_located((By.XPATH, product_title_xpath)))
            product_name = product_title_element.text.strip()
            logging.info(f"Nom du produit: '{product_name}'")
        except Exception as e:
            logging.warning(f"Impossible d'extraire le nom du produit: {e}")

        # --- 2. Cliquer "Voir les options d'achat" ---
        logging.info("Recherche 'Voir les options d'achat'...")
        try:
            options_button_xpath = "//button[contains(., 'Voir les options d')] | //a[contains(., 'Voir les options d')]"
            options_button = wait.until(EC.element_to_be_clickable((By.XPATH, options_button_xpath)))
            logging.info("Bouton 'Options' trouvé. Clic...")
            driver.execute_script("arguments[0].scrollIntoView(true);", options_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", options_button)
            logging.info("Bouton 'Options' cliqué via JS.")
            time.sleep(1)
        except TimeoutException:
            logging.error("Impossible de trouver/cliquer 'Voir les options d'achat'.")
            raise
        except Exception as e:
            logging.error(f"Erreur clic 'Options': {e}")
            raise

        # --- 3. Cliquer "Drive" dans Modale 1 ---
        logging.info("Attente modale 1 et recherche bouton 'Drive'...")
        try:
            drive_button_xpath = "//div[@role='dialog' or contains(@class, 'modal')]//button[contains(., 'Drive')]"
            drive_button = wait.until(EC.element_to_be_clickable((By.XPATH, drive_button_xpath)))
            logging.info("Bouton 'Drive' trouvé. Clic...")
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", drive_button)
            logging.info("Bouton 'Drive' cliqué via JS.")
            time.sleep(1.5)
        except TimeoutException:
            logging.error("Impossible de trouver/cliquer 'Drive' dans modale 1.")
            raise
        except Exception as e:
            logging.error(f"Erreur clic 'Drive': {e}")
            raise

        # --- 4. Interagir Modale 2 (Adresse) ---
        logging.info("Attente modale 2 (adresse)...")
        address_input_xpath = "//input[@placeholder='Ex: 34 rue de Monge, 75005']"
        try:
            logging.info(f"Attente champ saisie: {address_input_xpath}")
            address_input = wait.until(EC.visibility_of_element_located((By.XPATH, address_input_xpath)))
            logging.info("Champ saisie trouvé.")
            logging.info(f"Saisie code postal: {postal_code_to_search}")
            address_input.clear()
            address_input.send_keys(postal_code_to_search)
            logging.info("Code postal saisi.")
            time.sleep(1.5)
        except TimeoutException as e:
            logging.error(f"Timeout: Modale 2 ou champ input introuvable. {e}")
            raise
        except Exception as e:
            logging.error(f"Erreur saisie adresse: {e}")
            raise

        # --- 5. Sélectionner la 2ème Suggestion (XPath très spécifique) ---
        logging.info("Attente et sélection de la 2ème suggestion (1ère adresse)...")
        modal_updated_indicator_xpath = "//*[contains(text(), 'magasins proposés')]"
        try:
            target_suggestion_button_xpath = ("//ul[contains(@class, 'c-autocomplete__suggestions')]//li[2]//button[contains(@class, 'c-autocomplete__suggestion-button')]")
            logging.info(f"Attente du bouton de la 2ème suggestion: {target_suggestion_button_xpath}")
            target_suggestion_button = wait.until(EC.element_to_be_clickable((By.XPATH, target_suggestion_button_xpath)))
            try:
                suggestion_text = target_suggestion_button.find_element(By.XPATH, "./ancestor::li[1]").text.strip()
                logging.info(f"Bouton de la 2ème suggestion trouvé et cliquable: '{suggestion_text}'")
            except Exception:
                logging.info("Bouton de la 2ème suggestion trouvé et cliquable (texte non récupéré).")

            logging.info("Tentative de clic sur le bouton de la suggestion...")
            # Prioriser JS click
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", target_suggestion_button)
            logging.info("Clic JS sur le bouton de suggestion effectué.")

            logging.info("Vérification de l'apparition de la liste des magasins...")
            wait.until(EC.visibility_of_element_located((By.XPATH, modal_updated_indicator_xpath)))
            logging.info("La liste des magasins est apparue.")

        except TimeoutException:
            # Si le JS click échoue à mettre à jour, tenter ActionChains
            logging.warning("La liste des magasins n'est pas apparue après le clic JS. Tentative avec ActionChains...")
            try:
                time.sleep(0.5)
                # Il faut parfois re-localiser l'élément avant ActionChains
                target_suggestion_button = wait.until(EC.element_to_be_clickable((By.XPATH, target_suggestion_button_xpath)))
                actions = ActionChains(driver)
                actions.move_to_element(target_suggestion_button).pause(0.2).click().perform()
                logging.info("Clic via ActionChains effectué.")
                wait.until(EC.visibility_of_element_located((By.XPATH, modal_updated_indicator_xpath)))
                logging.info("La liste des magasins est apparue après ActionChains.")
            except Exception as action_err:
                logging.error(f"Le clic ActionChains a aussi échoué ou la liste magasins n'est pas apparue: {action_err}")
                raise TimeoutException("Impossible de confirmer le clic sur la suggestion et la mise à jour de la modale.") from action_err
        except Exception as e:
            logging.error(f"Erreur lors de la sélection de la 2ème suggestion: {e}")
            raise

        # --- 6. Cliquer sur le premier bouton "Choisir" ---
        logging.info("Recherche du premier bouton 'Choisir' dans la liste des magasins...")
        try:
            first_choose_button_xpath = "(//div[contains(@class, 'store-list')] | //ul[contains(@class, 'store-list')] | //div[@role='dialog'])//button[normalize-space()='Choisir'][1]"
            logging.info(f"Attente du premier bouton 'Choisir': {first_choose_button_xpath}")
            first_choose_button = wait.until(EC.element_to_be_clickable((By.XPATH, first_choose_button_xpath)))
            logging.info("Premier bouton 'Choisir' trouvé. Clic...")
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", first_choose_button)
            logging.info("Premier bouton 'Choisir' cliqué via JS.")

            modal_container_xpath = "//div[@role='dialog' and contains(., 'magasins proposés')]"
            logging.info("Attente de la disparition de la modale des magasins...")
            wait.until(EC.invisibility_of_element_located((By.XPATH, modal_container_xpath)))
            logging.info("Modale des magasins disparue.")
            time.sleep(2.0)  # Augmentation du délai pour s'assurer que la page est complètement chargée

        except TimeoutException:
            logging.error("Impossible de trouver/cliquer 'Choisir', ou la modale n'a pas disparu après.")
            raise
        except Exception as e:
            logging.error(f"Erreur lors du clic sur 'Choisir': {e}")
            raise

        # --- 7. Extraire le nom du magasin ---
        try:
            store_name_xpath = "//div[@id='data-service-crf-1']//div[contains(@class, 'delivery-choice__title-content')]"
            logging.info(f"Attente du nom du magasin sélectionné: {store_name_xpath}")
            store_name_element = wait.until(EC.visibility_of_element_located((By.XPATH, store_name_xpath)))
            store_name = store_name_element.text.strip()
            logging.info(f"Nom du magasin extrait: '{store_name}'")
        except Exception as e:
            logging.warning(f"Impossible d'extraire le nom du magasin: {e}")

        # --- 8. Extraire le prix par unité ---
        logging.info("Tentative d'extraction du prix par unité...")
        time.sleep(2)  # Attendre que la page soit complètement chargée
        
        try:
            # Méthode 0 (PRIORITAIRE): Extraire du JSON dans window.__INITIAL_STATE__
            logging.info("Extraction du prix depuis le JSON window.__INITIAL_STATE__")
            
            js_json_script = """
            try {
                const state = window.__INITIAL_STATE__;
                
                // Chercher l'EAN du produit à partir de l'URL actuelle
                const url = window.location.href;
                const eanMatch = url.match(/\\d{13}/);
                const ean = eanMatch ? eanMatch[0] : null;
                
                // Si nous avons trouvé l'EAN, chercher les détails du produit
                if (ean && state.vuex.analytics.indexedEntities.product && state.vuex.analytics.indexedEntities.product[ean]) {
                    const productData = state.vuex.analytics.indexedEntities.product[ean];
                    
                    // Chercher la première offre disponible
                    const offers = productData.attributes.offers[ean];
                    if (offers) {
                        const firstOfferId = Object.keys(offers)[0];
                        if (firstOfferId) {
                            const offer = offers[firstOfferId];
                            if (offer && offer.attributes && offer.attributes.price) {
                                return offer.attributes.price.perUnitLabel || null;
                            }
                        }
                    }
                }
                
                // Si on ne trouve pas avec l'approche structurée, on fait une recherche plus générique
                if (state.vuex.analytics.indexedEntities.offer) {
                    const offerEntities = state.vuex.analytics.indexedEntities.offer;
                    for (const offerId in offerEntities) {
                        const offer = offerEntities[offerId];
                        if (offer && offer.attributes && offer.attributes.price && offer.attributes.price.perUnitLabel) {
                            return offer.attributes.price.perUnitLabel;
                        }
                    }
                }
                
                return null;
            } catch (e) {
                console.error("Erreur lors de l'extraction JSON:", e);
                return null;
            }
            """
            price_per_unit_json = driver.execute_script(js_json_script)
            
            if price_per_unit_json:
                price_per_unit = price_per_unit_json
                logging.info(f"Prix extrait du JSON: '{price_per_unit}'")
            else:
                raise Exception("Pas de prix trouvé dans le JSON")
                
        except Exception as json_err:
            logging.warning(f"Échec extraction JSON: {json_err}")
            
            # Méthodes alternatives
            logging.info("Tentative avec méthodes alternatives...")
            try:
                # Méthode 1: XPath
                price_per_unit_xpath = "//p[contains(@class, 'product-title__per-unit-label')]"
                price_per_unit_element = driver.find_element(By.XPATH, price_per_unit_xpath)
                price_per_unit = price_per_unit_element.text.strip()
                logging.info(f"Prix extrait via XPath: '{price_per_unit}'")
            except Exception as xpath_err:
                logging.warning(f"Échec XPath: {xpath_err}")
                
                try:
                    # Méthode 2: CSS Selector
                    css_selector = "p.product-title__per-unit-label"
                    price_per_unit_element = driver.find_element(By.CSS_SELECTOR, css_selector)
                    price_per_unit = price_per_unit_element.text.strip()
                    logging.info(f"Prix extrait via CSS: '{price_per_unit}'")
                except Exception as css_err:
                    logging.warning(f"Échec CSS: {css_err}")
                    
                    try:
                        # Méthode 3: JavaScript
                        js_script = """
                        var elements = document.getElementsByClassName('product-title__per-unit-label');
                        if (elements && elements.length > 0) {
                            return elements[0].textContent.trim();
                        } else {
                            return "Non trouvé via JS";
                        }
                        """
                        price_per_unit = driver.execute_script(js_script)
                        logging.info(f"Prix extrait via JS: '{price_per_unit}'")
                        
                        if price_per_unit == "Non trouvé via JS":
                            # Méthode 4: Contenu
                            try:
                                euro_element_xpath = "//*[contains(text(), '€ / L') or contains(text(), '€/L')]"
                                euro_element = driver.find_element(By.XPATH, euro_element_xpath)
                                price_per_unit = euro_element.text.strip()
                                logging.info(f"Prix trouvé par contenu: '{price_per_unit}'")
                            except Exception as content_err:
                                logging.error(f"Échec méthode contenu: {content_err}")
                                price_per_unit = "N/A (extraction impossible)"
                    except Exception as js_err:
                        logging.error(f"Échec méthode JS: {js_err}")
                        price_per_unit = "N/A (extraction impossible)"

        # --- 9. Sauvegarde CSV ---
        data_to_save = [postal_code_to_search, store_name, price_per_unit, product_name, product_url]
        write_to_csv(data_to_save)
        logging.info("Données enregistrées dans le CSV.")

        # --- 10. Attente finale ---
        logging.info("Script terminé avec succès.")
        return True

    # --- Gestion Erreurs et Finally ---
    except Exception as e:
        logging.critical(f"Une erreur générale s'est produite: {e} pour {postal_code_to_search} - {product_url}")
        if store_name != "N/A" or price_per_unit != "N/A":
            logging.info("Tentative de sauvegarde des données partielles avant de quitter...")
            data_to_save = [postal_code_to_search, store_name, price_per_unit, product_name, product_url]
            write_to_csv(data_to_save)
        return False
    finally:
        if driver:
            driver.quit()
            logging.info(f"Navigateur fermé pour {postal_code_to_search} - {product_url}")

def process_batch(tasks_batch):
    """Traite un batch de tâches séquentiellement dans un processus dédié."""
    for task in tasks_batch:
        product_url, postal_code = task
        try:
            logging.info(f"Traitement de {product_url} pour CP {postal_code}")
            visiter_produit_et_choisir_drive((product_url, postal_code))
            # Pause entre chaque exécution pour éviter de surcharger le site
            time.sleep(5)  # Pause réduite pour accélérer le traitement
        except Exception as e:
            logging.error(f"Erreur lors du traitement de {product_url} pour {postal_code}: {e}")
            logging.info("Passage à la combinaison suivante...")
            continue

def create_task_batches(products, postal_codes, num_workers=8):
    """Crée des batches de tâches équilibrés pour un nombre de workers donné."""
    all_tasks = [(product, code) for product in products for code in postal_codes]
    total_tasks = len(all_tasks)
    batch_size = total_tasks // num_workers
    
    if batch_size == 0:
        batch_size = 1
    
    batches = []
    for i in range(0, total_tasks, batch_size):
        end = min(i + batch_size, total_tasks)
        batches.append(all_tasks[i:end])
    
    # Assurer qu'on n'a pas plus de batches que de workers
    while len(batches) > num_workers:
        batches[-2].extend(batches[-1])
        batches.pop()
    
    return batches

if __name__ == "__main__":
    # Supprimer le fichier CSV existant pour éviter de mélanger les données
    if os.path.exists(CSV_FILENAME):
        try:
            os.remove(CSV_FILENAME)
            logging.info(f"Ancien fichier {CSV_FILENAME} supprimé.")
        except Exception as e:
            logging.error(f"Impossible de supprimer l'ancien fichier CSV: {e}")
    
    # Créer les batches de tâches
    NUM_WORKERS = 8
    task_batches = create_task_batches(PRODUITS, CODES_POSTAUX, NUM_WORKERS)
    
    logging.info(f"Lancement du traitement avec {NUM_WORKERS} workers.")
    logging.info(f"Nombre total de tâches: {sum(len(batch) for batch in task_batches)}")
    
    # Exécuter les batches en parallèle
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(process_batch, batch) for batch in task_batches]
        
        # Attendre la fin de tous les processus
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                future.result()
                logging.info(f"Batch {i+1}/{NUM_WORKERS} terminé avec succès")
            except Exception as e:
                logging.error(f"Batch {i+1}/{NUM_WORKERS} a échoué: {e}")
    
    logging.info("========== TRAITEMENT TERMINÉ POUR TOUS LES PRODUITS ET CODES POSTAUX ==========")