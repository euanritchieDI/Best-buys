library(openxlsx)
library(readxl)
library(WDI)
library(httr)
library(jsonlite)
library(tictoc) # for measuring run time
library(glue)
library(data.table)
library(tidyverse)
library(readtext)
library(janitor)

#########################################################

## THIS BIT GETS EDUCATION ID CODES. COULD DO THIS FROM API BUT QUICKER AND 
## EASIER TO GET FROM DOWNLOADING PROJECT LIST FROM WB WEBSITE

#wbnew = read_excel("C:/Users/euan.ritchie/Downloads/all (2).xls",skip=2)
#wbnew$educ = 1*(grepl("ducation",wbnew$sector1))
#wbnew$educ2 = 1*(grepl("ducation",wbnew$sector1))
#wbnew$educ2[grepl("ducation",wbnew$sector2)] = 1
#wbnew$educ2[grepl("ducation",wbnew$sector3)] = 1

##... however some projects seem to have disappeared relative to last download...
wb = read_excel("GitHub/Best-buys/World Bank/data/WB_projects_21_10_2024.xls",skip=2)
wb$educ = 1*(grepl("ducation",wb$sector1))
wb$educ2 = 1*(grepl("ducation",wb$sector1))
wb$educ2[grepl("ducation",wb$sector2)] = 1
wb$educ2[grepl("ducation",wb$sector3)] = 1

educs = unique(c(wb$id[wb$educ==1]))
educs2 = unique(c(wb$id[wb$educ2==1]))

setnames(wb,"id","projectid")

# educs from wb best buys code

#educs = "P123456,P234567,P345678"
stub="https://search.worldbank.org/api/v2/wds?format=json&includepublicdocs=1&fl=*&os=0&rows=500&proid="

tic()
lnk = paste0(stub,educs2[1])
req     = GET(url = lnk)
res     = content(req, as = "text", encoding = "UTF-8")
json    = fromJSON(res, flatten = TRUE)
docjson = json

for (i in educs2[-1]){
	lnk = paste0(stub,i)
	req     = GET(url = lnk)
	res     = content(req, as = "text", encoding = "UTF-8")
	json    = fromJSON(res, flatten = TRUE)
	docjson = Map(c,docjson,json)
}		
toc()

doclist = names(docjson$documents)
doclist = unique(doclist[doclist!="facets"])

sel = c("majdocty","docty","docdt","display_title","projectid","txturl","pdfurl","repnb","prdln",
"projn","id")

docs = list()
for (i in doclist){
	jsonex = eval(parse(text=paste0("docjson$documents$",i)))
	docs[[i]] = jsonex[sel]
}

dats = as.data.frame(rbindlist(docs,fill=T))

pads = dats[dats$docty=="Project Appraisal Document",]
pads = pads[!is.na(pads$projectid),]
pads = remove_empty(pads, which = c("cols", "rows"))

tic()
cnt = 0
padtext  =NULL
for (i in pads$txturl){
	toadd = tryCatch(readtext(i,encoding="Windows-1252")[,2],error=function(e) "fail")
	padtext = c(padtext,toadd)
	cnt = cnt+1
	if(cnt%%20==0){print(cnt)}
}
toc()

#-------------------------------------------------
#STRING FUNCTIONS
remove_punct = function(string){
  str_replace_all(string, "[[:punct:]]", " ")
}
collapse_whitespace = function(string){
  str_replace_all(string, "\\s+", " ")
}
#-------------------------------------------------

padtext = remove_punct(collapse_whitespace(padtext))
padtext = tolower(padtext)

#stped   = str_count(padtext,"structured ?pedagogy")

SP = c("structured.?pedagogy",
  "structured.?pedagogical.?interventions", 
  #“lesson plans” & “learning materials/student books” & “coaching/instructional support” 
  "structured.?lesson.?plans",
  "pedagogical.?guidance",
  "ongoing.?teacher.?support",
  "standardized.?approach",
  "packaged.?intervention",
  "lesson.?sequencing")

TARL = c(
  "group(ed|ing)? by ((learning|ability) level|level of (learning|ability))",
  "targeted ?instruction|instruction ?(that|which) ?is ?targeted",
  "teaching ?at ?the ?right ?level|\\btarl\\b",
  "level.?appropriate ?(tuition|instruction)",
  "catch.?up.?class",
  "interactive ?pedagogy",
  "remedial ?education",
  "differentiated ?instruction",
  "personali.ed ?learning")

INFO = c(
  "information.?treatment", 
  "information.?campaign",
  "targeted.?information.?dissemination",
  "school.?quality.?information", 
  "information.?about.?earnings", 
  "diagnostic.?feedback")

TT = c(
  "travel.?time.?reduction",
  "school.?proximity",
  "community.?schools",
  "transport.?assistance",
  "providing.?transportation",
  "village.?run.?schools",
  "safe school.?travel",
  "reduce.?distance.?to.?school",
  "remote.?areas.{0,60}(access.?to.?schooling|accessing.?school)|access.?to.?schooling.{0,60}remote.?areas")

test = padtext[157]
comfunk = function(x,reg){
	ret = ifelse(max(str_count(x,reg))==0,"",reg[which.max(str_count(x,reg))])
	return(ret)
}

comfunk(test,SP)

pads$stped     = str_count(padtext,paste(SP,collapse="|"))
pads$stped_var = sapply(padtext,function(x) sum(str_count(x,SP)>0))
pads$stped_com = sapply(padtext,function(x) comfunk(x,SP))
pads$tarl      = str_count(padtext,paste(TARL,collapse="|"))
pads$tarl_var  = sapply(padtext,function(x) sum(str_count(x,TARL)>0))
pads$tarl_com  = sapply(padtext,function(x) comfunk(x,TARL))
pads$info      = str_count(padtext,paste(INFO,collapse="|"))
pads$info_var  = sapply(padtext,function(x) sum(str_count(x,INFO)>0))
pads$info_com  = sapply(padtext,function(x) comfunk(x,INFO))
pads$travel      = str_count(padtext,paste(TT,collapse="|"))
pads$travel_var  = sapply(padtext,function(x) sum(str_count(x,TT)>0))
pads$travel_com  = sapply(padtext,function(x) comfunk(x,TT))


pads$preprim = preprim
pads$tarl    = tarl
pads$stped   = stped
pads$docyear = year(pads$docdt)
pads$totalchar = nchar(padtext)
pads$display_title = gsub("\\s{2,}"," ",pads$display_title)
pads$mainsec = 1*(pads$projectid %in% educs)
pads$anyBB = with(pads,1*(preprim>0 | stped>0 | tarl>0))
pads$anyBB_nopreprim = with(pads,1*(stped>0 | tarl>0))


as.data.frame(pads %>% group_by(year) %>% summarize(mean(totalchar)))



pads = left_join(pads,wb[c("projectid","boardapprovaldate","curr_total_commitment","sector1")],by="projectid")

write.csv(pads,"GitHub/Best-buys/World Bank/data/WorldBank_Education_projects_extra_vars.csv",row.names=F)
as.data.frame(pads %>% group_by(docyear) %>% summarize(mean(stped)))

with(pads,table(docyear,tarl))


justrelevant = pads %>% filter(tarl>0 | preprim>0 | stped>0)






