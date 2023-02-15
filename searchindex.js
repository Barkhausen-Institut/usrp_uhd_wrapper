Search.setIndex({docnames:["architecture","index","modules","setup","synchronisation","uhd_wrapper","uhd_wrapper.rpc_server","uhd_wrapper.utils","usrp_client"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":5,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":3,"sphinx.domains.rst":2,"sphinx.domains.std":2,"sphinx.ext.todo":2,sphinx:56},filenames:["architecture.rst","index.rst","modules.rst","setup.rst","synchronisation.rst","uhd_wrapper.rst","uhd_wrapper.rpc_server.rst","uhd_wrapper.utils.rst","usrp_client.rst"],objects:{"":[[5,0,0,"-","uhd_wrapper"],[8,0,0,"-","usrp_client"]],"uhd_wrapper.rpc_server":[[6,0,0,"-","reconfigurable_usrp"],[6,0,0,"-","rpc_server"]],"uhd_wrapper.rpc_server.reconfigurable_usrp":[[6,1,1,"","MimoReconfiguringUsrp"],[6,1,1,"","RestartingUsrp"]],"uhd_wrapper.rpc_server.reconfigurable_usrp.MimoReconfiguringUsrp":[[6,2,1,"","__init__"],[6,2,1,"","setRfConfig"]],"uhd_wrapper.rpc_server.reconfigurable_usrp.RestartingUsrp":[[6,3,1,"","RestartTrials"],[6,3,1,"","SleepTime"],[6,2,1,"","__init__"],[6,2,1,"","collect"],[6,2,1,"","execute"],[6,2,1,"","getCurrentFpgaTime"],[6,2,1,"","getCurrentSystemTime"],[6,2,1,"","getMasterClockRate"],[6,2,1,"","getRfConfig"],[6,2,1,"","resetStreamingConfigs"],[6,2,1,"","setRfConfig"],[6,2,1,"","setRxConfig"],[6,2,1,"","setSyncSource"],[6,2,1,"","setTimeToZeroNextPps"],[6,2,1,"","setTxConfig"]],"uhd_wrapper.rpc_server.rpc_server":[[6,4,1,"","RfConfigFromBinding"],[6,4,1,"","RfConfigToBinding"],[6,1,1,"","UsrpServer"]],"uhd_wrapper.rpc_server.rpc_server.UsrpServer":[[6,2,1,"","__init__"],[6,2,1,"","collect"],[6,2,1,"","configureRfConfig"],[6,2,1,"","configureRx"],[6,2,1,"","configureTx"],[6,2,1,"","execute"],[6,2,1,"","getCurrentFpgaTime"],[6,2,1,"","getCurrentSystemTime"],[6,2,1,"","getMasterClockRate"],[6,2,1,"","getRfConfig"],[6,2,1,"","resetStreamingConfigs"],[6,2,1,"","setSyncSource"],[6,2,1,"","setTimeToZeroNextPps"]],"uhd_wrapper.utils":[[7,0,0,"-","config"],[7,0,0,"-","serialization"]],"uhd_wrapper.utils.config":[[7,1,1,"","MimoSignal"],[7,1,1,"","RfConfig"],[7,1,1,"","RxStreamingConfig"],[7,1,1,"","TxStreamingConfig"],[7,4,1,"","rxContainsClippedValue"],[7,4,1,"","txContainsClippedValue"]],"uhd_wrapper.utils.config.MimoSignal":[[7,2,1,"","__init__"],[7,2,1,"","deserialize"],[7,2,1,"","serialize"],[7,3,1,"","signals"]],"uhd_wrapper.utils.config.RfConfig":[[7,2,1,"","__init__"],[7,2,1,"","deserialize"],[7,2,1,"","from_dict"],[7,2,1,"","from_json"],[7,3,1,"","noRxAntennas"],[7,3,1,"","noTxAntennas"],[7,3,1,"","rxAnalogFilterBw"],[7,3,1,"","rxCarrierFrequency"],[7,3,1,"","rxGain"],[7,3,1,"","rxSamplingRate"],[7,2,1,"","schema"],[7,2,1,"","serialize"],[7,2,1,"","to_dict"],[7,2,1,"","to_json"],[7,3,1,"","txAnalogFilterBw"],[7,3,1,"","txCarrierFrequency"],[7,3,1,"","txGain"],[7,3,1,"","txSamplingRate"]],"uhd_wrapper.utils.config.RxStreamingConfig":[[7,2,1,"","__init__"],[7,3,1,"","noSamples"],[7,3,1,"","receiveTimeOffset"]],"uhd_wrapper.utils.config.TxStreamingConfig":[[7,2,1,"","__init__"],[7,3,1,"","samples"],[7,3,1,"","sendTimeOffset"]],"uhd_wrapper.utils.serialization":[[7,5,1,"","SerializedComplexArray"],[7,4,1,"","deserializeComplexArray"],[7,4,1,"","serializeComplexArray"]],"usrp_client.MimoSignal":[[8,2,1,"","__init__"],[8,2,1,"","deserialize"],[8,2,1,"","serialize"],[8,3,1,"","signals"]],"usrp_client.RfConfig":[[8,2,1,"","__init__"],[8,2,1,"","deserialize"],[8,2,1,"","from_dict"],[8,2,1,"","from_json"],[8,3,1,"","noRxAntennas"],[8,3,1,"","noTxAntennas"],[8,3,1,"","rxAnalogFilterBw"],[8,3,1,"","rxCarrierFrequency"],[8,3,1,"","rxGain"],[8,3,1,"","rxSamplingRate"],[8,2,1,"","schema"],[8,2,1,"","serialize"],[8,2,1,"","to_dict"],[8,2,1,"","to_json"],[8,3,1,"","txAnalogFilterBw"],[8,3,1,"","txCarrierFrequency"],[8,3,1,"","txGain"],[8,3,1,"","txSamplingRate"]],"usrp_client.RxStreamingConfig":[[8,2,1,"","__init__"],[8,3,1,"","noSamples"],[8,3,1,"","receiveTimeOffset"]],"usrp_client.System":[[8,2,1,"","__init__"],[8,2,1,"","addUsrp"],[8,3,1,"","baseTimeOffsetSec"],[8,2,1,"","collect"],[8,2,1,"","configureRx"],[8,2,1,"","configureTx"],[8,2,1,"","execute"],[8,2,1,"","getCurrentFpgaTimes"],[8,2,1,"","getRfConfigs"],[8,2,1,"","getSupportedSamplingRates"],[8,2,1,"","newUsrp"],[8,2,1,"","resetFpgaTimes"],[8,3,1,"","syncAttempts"],[8,3,1,"","syncThresholdSec"],[8,3,1,"","syncTimeOut"],[8,2,1,"","synchronisationValid"],[8,3,1,"","timeBetweenSyncAttempts"]],"usrp_client.TxStreamingConfig":[[8,2,1,"","__init__"],[8,3,1,"","samples"],[8,3,1,"","sendTimeOffset"]],"usrp_client.UsrpClient":[[8,2,1,"","__init__"],[8,2,1,"","configureRfConfig"],[8,2,1,"","create"],[8,2,1,"","execute"],[8,2,1,"","getSupportedDecimationRatios"],[8,2,1,"","getSupportedSamplingRates"]],"usrp_client.errors":[[8,6,1,"","MultipleRemoteUsrpErrors"],[8,6,1,"","RemoteUsrpError"]],"usrp_client.errors.MultipleRemoteUsrpErrors":[[8,2,1,"","__init__"]],"usrp_client.errors.RemoteUsrpError":[[8,2,1,"","__init__"]],"usrp_client.rpc_client":[[8,1,1,"","UsrpClient"]],"usrp_client.rpc_client.UsrpClient":[[8,2,1,"","__init__"],[8,2,1,"","configureRfConfig"],[8,2,1,"","create"],[8,2,1,"","execute"],[8,2,1,"","getSupportedDecimationRatios"],[8,2,1,"","getSupportedSamplingRates"]],"usrp_client.system":[[8,1,1,"","LabeledUsrp"],[8,1,1,"","System"],[8,1,1,"","TimedFlag"]],"usrp_client.system.LabeledUsrp":[[8,3,1,"","client"],[8,3,1,"","ip"],[8,3,1,"","name"],[8,3,1,"","port"]],"usrp_client.system.System":[[8,2,1,"","__init__"],[8,2,1,"","addUsrp"],[8,3,1,"","baseTimeOffsetSec"],[8,2,1,"","collect"],[8,2,1,"","configureRx"],[8,2,1,"","configureTx"],[8,2,1,"","execute"],[8,2,1,"","getCurrentFpgaTimes"],[8,2,1,"","getRfConfigs"],[8,2,1,"","getSupportedSamplingRates"],[8,2,1,"","newUsrp"],[8,2,1,"","resetFpgaTimes"],[8,3,1,"","syncAttempts"],[8,3,1,"","syncThresholdSec"],[8,3,1,"","syncTimeOut"],[8,2,1,"","synchronisationValid"],[8,3,1,"","timeBetweenSyncAttempts"]],"usrp_client.system.TimedFlag":[[8,2,1,"","__init__"],[8,2,1,"","isSet"],[8,2,1,"","reset"],[8,2,1,"","set"]],uhd_wrapper:[[6,0,0,"-","rpc_server"],[7,0,0,"-","utils"]],usrp_client:[[8,1,1,"","MimoSignal"],[8,1,1,"","RfConfig"],[8,1,1,"","RxStreamingConfig"],[8,1,1,"","System"],[8,1,1,"","TxStreamingConfig"],[8,1,1,"","UsrpClient"],[8,0,0,"-","errors"],[8,0,0,"-","rpc_client"],[8,0,0,"-","system"]]},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","method","Python method"],"3":["py","attribute","Python attribute"],"4":["py","function","Python function"],"5":["py","data","Python data"],"6":["py","exception","Python exception"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:attribute","4":"py:function","5":"py:data","6":"py:exception"},terms:{"0":[1,4,7,8],"1":[1,4,7,8],"10":[1,3],"10k":1,"10mhz":3,"1200":8,"2":[1,4,8],"20":8,"2s":8,"3":[4,8],"30db":3,"4x4":1,"5":[1,6],"5555":[1,3,8],"9":1,"byte":[7,8],"case":1,"class":[6,7,8],"default":[3,7,8],"do":8,"float":[6,7,8],"function":[1,4,7,8],"import":3,"int":[6,7,8],"new":8,"return":[7,8],"static":[7,8],"true":[7,8],"while":1,A:[7,8],As:[1,3,4],For:8,IN:3,If:[1,4,8],In:[0,1,4,8],It:[1,3,4],On:[0,1,4],One:[1,7],The:[1,3,4,8],There:3,To:[0,1],__init__:[6,7,8],_rpcclient:8,abov:[0,7],absolut:7,accept:4,access:[4,8],activ:1,actual:[0,4,8],actualusrpmsg:8,ad:[4,8],add:[1,3,4,8],address:1,addusrp:[4,8],adjust:1,advis:3,affili:1,after:[1,4,8],afterward:[1,4],again:1,against:[0,1],alia:[7,8],all:[1,8],allow_nan:[7,8],also:1,although:3,alwai:1,an:[4,8],analys:1,analysi:1,analyz:1,antenna:[1,3,7,8],api:[0,4,7,8],ar:[0,1,3,4,8],architectur:[1,8],argument:1,arrai:[7,8],arriv:4,assum:[1,4],attemp:8,attempt:8,attenu:3,barkhausen:1,base:[4,6,7,8],basetim:[6,8],basetimeoffsetsec:8,below:1,better:1,between:[3,8],bin:1,bind:0,block:[1,4,8],blue:0,bool:[7,8],box:[0,1],buffer:[1,8],bugfix:1,build:1,built:[1,4],burst:1,bytearrai:[7,8],cabl:3,calcul:8,call:[0,4,8],callabl:[7,8],can:[1,3,4,8],capabl:1,carrier:[1,4],cast:4,cd:1,certain:8,cf:[1,4],chang:[3,8],channel:3,check:[1,4,7],check_circular:[7,8],classmethod:[7,8],client:[0,3,8],clock:[3,4],clone:1,cmake:1,code:[0,1,4],collect:[1,4,6,8],command:1,commun:[0,1,3,8],compar:8,complex:7,conduct:1,config:[1,2,5,6,8],configur:[0,1,4,7,8],configurerfconfig:[6,8],configurerx:[4,6,8],configuretx:[4,6,8],conjunct:1,connect:[3,8],consid:8,consist:4,constant:4,constructor:8,contain:[1,7,8],content:2,context:[7,8],correspond:[1,7,8],cover:1,creat:[0,1,4,8],ctest:1,current:8,custom:0,data:[3,7],dataclass:[1,4],dataclasses_json:[7,8],datatyp:7,dcmake_build_typ:1,debug:1,decim:8,dedic:1,defin:[4,8],delai:1,denot:8,depend:1,depict:[0,4],deploi:1,descript:[1,4],deseri:[7,8],deserializecomplexarrai:7,design:1,desir:[3,8],desireddevicetyp:6,desiredtyp:6,detect:4,determinist:1,develop:8,devic:[0,1,4,8],dict:[7,8],dictionari:8,differ:[1,8],dimension:7,direct:8,directli:1,directori:1,distribut:1,doe:1,done:[1,3],driver:[0,1],dump:1,dump_onli:[7,8],e:1,each:[1,4,7,8],eas:0,easi:1,edg:4,effect:3,element:7,emphas:1,enabl:1,encode_json:[7,8],enough:1,ensur:[1,3],ensure_ascii:[7,8],env:1,environ:1,error:2,etc:[1,8],evalu:1,even:3,exampl:4,except:8,exclud:[7,8],execut:[1,4,6,8],exist:8,explanatori:1,explicit:4,extern:4,factori:[7,8],fals:[7,8],fast:1,feedback:1,field:8,file:1,finish:4,first:[1,7],flag:8,fledg:1,folder:1,follow:[1,3,4],forward:8,found:1,four:1,fpga:[1,4,8],frame:[1,7,8],frequenc:[1,4],from:[1,4],from_dict:[7,8],from_json:[7,8],frontend:[1,8],full:1,further:1,g:1,gener:3,get:3,getcurrentfpgatim:[6,8],getcurrentsystemtim:6,getmasterclockr:6,getrfconfig:[6,8],getsupporteddecimationratio:8,getsupportedsamplingr:8,git:1,give:[1,8],given:8,green:4,grei:0,ha:4,had:1,happen:1,hardwar:1,have:[1,4],henc:8,henceforth:0,her:1,here:[1,4],hi:1,high:0,highli:1,highlight:[0,4],hood:[0,8],hostnam:3,howev:1,i:1,identifi:8,illustr:4,imag:4,implement:[1,4,8],indent:[7,8],independ:1,index:1,infer_miss:[7,8],instead:1,institut:1,integr:[0,1],interfac:8,intern:4,interv:4,involv:3,ip:[1,3,6,8],isset:8,item:[7,8],itself:[1,4],j4:1,jca:[1,4],joint:1,just:1,kei:8,kronauer:1,kv:[7,8],kw:[7,8],labeledusrp:8,laptop:[0,1],least:1,length:3,less:1,like:1,limit:1,linux:1,list:[6,7,8],listen:8,load_onli:[7,8],local:1,localhost_transmiss:1,locat:1,loglevel:8,look:4,m:1,made:1,mai:1,main:8,mainli:[1,8],make:[1,3],manag:0,mani:[7,8],match:7,matth:1,maximilian:1,mean:1,meant:1,measur:1,meinberg:3,memori:1,messag:1,method:8,mhz:3,mimo:1,mimo_p2p_transmiss:1,mimoreconfiguringusrp:6,mimosign:[7,8],minor:1,minut:1,mitig:3,mkdir:1,mm:[7,8],modif:1,modul:[0,1,2],more:[1,8],most:1,multi:4,multipl:[4,8],multipleremoteusrperror:8,must:7,name:[1,8],ndarrai:[6,7,8],need:[1,4,7],network:1,newusrp:8,next:[4,8],nois:1,non:7,none:[6,7,8],norxantenna:[7,8],nosampl:[6,7,8],note:[1,3,4],notxantenna:[7,8],np:[7,8],number:[7,8],numpi:[6,7,8],object:[6,7,8],occur:1,offset:[4,8],omit:1,onc:[1,4],one:[1,7,8],onedimension:7,onli:[1,7,8],ooutput:3,open:3,option:[1,7,8],order:[0,4,8],other:1,our:1,out:[1,3],own:4,packag:[1,2,4],packet:3,page:1,paramet:[7,8],parse_const:[7,8],parse_float:[7,8],parse_int:[7,8],parti:0,partial:[7,8],pass:[0,1],pattern:1,peer:1,per:[1,4],perform:0,physic:1,pictur:[0,4],pip:1,plenti:1,plot:1,point:1,polish:1,port:[1,3,4,8],post:1,pp:[3,4,8],preliminari:3,prepar:8,previou:1,print:1,privat:8,proce:1,procedur:[0,8],process:[0,1],properli:8,protocol:[0,8],provid:[1,4],pseudo:4,puls:4,py:1,pytest:1,python3:1,python:[0,1,7],queri:8,r:1,radio:[1,3,8],rais:7,random:1,rate:[1,8],ratio:8,read:1,real:7,receiv:[1,3,8],receivetimeoffset:[4,6,7,8],recommend:1,reconfigurable_usrp:[2,5],ref:3,refer:[3,8],relat:1,releas:1,remot:[0,8],remoteusrperror:8,replai:1,repli:4,repo:1,repositori:1,repres:8,request:[4,8],requir:[7,8],requirements_test:1,reset:[4,8],resetfpgatim:8,resetstreamingconfig:6,resettimesec:8,respect:[4,8],restart:[1,3],restartingusrp:6,restarttri:6,reus:4,rf:1,rfconfig:[6,7,8],rfconfigbind:6,rfconfigfrombind:6,rfconfigtobind:6,rfnoc:1,row:1,rpc:[0,1,7,8],rpc_client:2,rpc_server:[2,5],run:[0,1,3,8],rusrp1:4,rusrp2:4,rusrp3:4,rusrp4:4,rx0:3,rxanalogfilterbw:[7,8],rxcarrierfrequ:[7,8],rxconfig:6,rxcontainsclippedvalu:7,rxgain:[7,8],rxsamplingr:[7,8],rxstreamingconfig:[4,6,7,8],s:[7,8],same:[3,8],sampel:1,sampl:[1,4,6,7,8],samplesmulticast:4,samplesunicast:4,scenario:1,schema:[7,8],schemaf:[7,8],search:1,second:[1,4,7],section:1,self:1,send:[1,4,8],sendtimeoffset:[4,6,7,8],sens:1,sent:1,separ:[7,8],serial:[1,2,5,8],serializecomplexarrai:7,serializedcomplexarrai:7,serializedrfconfig:6,serv:1,server:[0,3,8],servic:1,set:[1,4,8],setrfconfig:6,setrxconfig:6,setsyncsourc:6,settimetozeronextpp:6,settxconfig:6,shift:1,should:[1,3,8],show:4,side:[1,3,8],signal:[0,1,3,4,7,8],sinc:[1,7],siso:1,skipkei:[7,8],sleep:8,sleeptim:6,snippet:1,softwar:1,some:1,somebodi:1,sort_kei:[7,8],specifi:8,spectrum:1,ssh:[1,3],std:1,step:[1,3],stop:1,str:[6,7,8],stream:[1,4,8],strongli:1,submodul:[2,5],subpackag:2,suffici:1,support:[1,8],sure:3,sync:4,syncattempt:8,synchron:[3,4,8],synchronis:[1,8],synchronisationvalid:8,syncsourc:6,syncthresholdsec:8,synctimeout:8,synctyp:6,system:[0,2,4],systemctl:1,t0:4,taken:8,tcp:3,test:1,than:8,thei:[1,4],them:[1,8],therefor:[1,3],thi:[0,1,3,4,7,8],third:0,throughput:0,thrown:8,time:[1,4,8],timebetweensyncattempt:8,timedflag:8,timeout:8,timestamp:8,to_dict:[7,8],to_json:[7,8],tobia:1,top:[1,4],touch:1,transmiss:[1,4,8],transmit:[1,3,4],transmitt:8,trigger:4,tupl:[6,7,8],tusrp1:4,two:[1,3,4,8],tx:3,tx_stream:1,txanalogfilterbw:[7,8],txcarrierfrequ:[7,8],txconfig:6,txcontainsclippedvalu:7,txgain:[7,8],txsamplingr:[7,8],txstreamingconfig:[4,6,7,8],txt:1,type:[3,7,8],uh:0,uhd_wrapp:[1,2,8],under:[0,8],underflow:1,unicast:4,union:[7,8],univers:1,unknown:[7,8],until:8,upon:8,us:[0,3,7,8],usag:1,usecas:1,user:[1,8],usrp1:[1,4],usrp1_ip:1,usrp2:[1,4],usrp2_ip:1,usrp3:4,usrp4:4,usrp:[0,3,4,6,7,8],usrp_client:[1,2,4],usrp_p2p_transmiss:1,usrp_pybind:6,usrpclient:8,usrpnam:[4,8],usrpserv:[6,8],usual:4,util:[1,2,5,6,8],v:1,valid:8,valu:[7,8],valueerror:7,variabl:1,venv:1,verifi:[1,8],vi:3,via:[0,1,3,4],virtual:1,wa:1,wait:[4,8],want:[1,4],we:[0,1,3,4,7,8],weak:3,welcom:1,well:1,when:8,where:8,wherea:0,which:[0,1,4,8],white:1,wide:0,within:4,without:4,workflow:4,wrap:[0,1,8],wrapper:1,x410:[1,6],you:[1,3,4,8],your:[1,3,4,8],zero:4,zeromq:[0,3,8],zerorpc:[0,7,8]},titles:["Software Architecture","Usrp UHD Api","usrp_uhd_wrapper","Physical &amp; Network Setup","Synchronisation &amp; Communication Patterns","uhd_wrapper package","uhd_wrapper.rpc_server package","uhd_wrapper.utils package","usrp_client package"],titleterms:{For:1,alreadi:1,api:1,architectur:0,author:1,befor:1,chang:1,client:1,commun:4,config:7,content:[5,6,7,8],develop:1,document:1,error:8,exampl:1,get:1,hardware_test:1,histori:1,indic:1,instal:1,modul:[5,6,7,8],network:3,packag:[5,6,7,8],pattern:4,physic:3,purpos:1,reconfigurable_usrp:6,rpc_client:8,rpc_server:6,serial:7,server:1,setup:[1,3],softwar:0,start:1,submodul:[6,7,8],subpackag:5,synchronis:4,system:8,tabl:1,uhd:1,uhd_wrapp:[5,6,7],us:1,usrp:1,usrp_client:8,usrp_uhd_wrapp:2,util:7}})