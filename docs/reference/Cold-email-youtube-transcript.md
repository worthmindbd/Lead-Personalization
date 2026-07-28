 Cold  email  always  has  a  trade-off.  You 
 either  send  high-volume  and  accept  that 
 emails  are  generic  or  you  write  deeply 
 personalized  messages  and  accept  that 
 you're  only  sending  a  few  dozen  a  day. 
 Both  have  a  ceiling.  Generic  volume  gets 
 ignored.  Personalized  but  small  doesn't 
 scale.  What  I'm  going  to  show  you  in 
 this  video  is  how  to  break  that 
 trade-off  completely.  We've  helped  a  lot 
 of  people  run  cold  email  campaigns 
 through  Instantly  and  the  accounts  that 
 consistently  get  the  highest  success 
 outcomes  usually  have  two  things  in 
 common:  personalization  and  relevance. 
 Most  people's  personalization  looks  like 
 this.  Hey  first  name,  I  noticed  you  work 
 at  company.  That  is  not  personalization. 
 That  is  a  mail  merge.  It's  automated 
 name-dropping  and  the  person  reading  it 
 has  seen  some  version  of  it  thousands  of 
 times.  Real  personalization  references 
 something  specific.  Maybe  it's  a  recent 
 post  they  made.  Maybe  it's  a  new  hire. 
 That's  what  gets  someone  to  pause.  But 
 even  then,  personalization  by  itself  is 
 not  the  whole  game.  The  real  question  is 
 whether  a  message  creates  enough 
 relevance  and  enough  value  to  make 
 somebody  want  to  engage  further.  When 
 you're  sending  a  cold  email,  you're  not 
 just  trying  to  get  replies.  You're 
 trying  to  create  outcomes.  And  what 
 Claude  Code  lets  us  do  is  create  that 
 exact  copy  at  a  scale  that  used  to 
 require  a  team  of  VAs  doing  manual 
 research  all  day.  Now,  you  might  be 
 wondering,  why  Claude  Code  specifically? 
 The  short  version  is  that  Claude  Code  is 
 not  just  a  normal  chat  interface  where 
 you  paste  in  text  and  hope  it  gives  you 
 something  useful  back.  Claude  Code  can 
 actually  work  through  multi-step  tasks. 
 It  can  browse,  collect  context,  research 
 prospects,  and  then  turn  that  research 
 into  personalized  output.  And  for  this 
 workflow,  that  matters  a  lot.  Because  if 
 you  want  to  send  1,000  emails  per  day  to 
 a  cold  audience,  you  need  enough  volume 
 to  get  enough  data.  If  you  send  too 
 little,  you  don't  really  know  what's 
 working.  You  don't  know  if  the  problem 
 is  the  offer,  the  list,  the  messaging, 
 the  deliverability,  or  just  the  low 
 sample  size.  At  1,000  emails  per  day, 
 now  you're  getting  signal.  Now  you  can 
 start  learning  what  markets  respond, 
 what  angles  produce  interest,  what 
 messaging  creates  action,  and  whether 
 your  campaign  is  actually  producing 
 outcomes.  First  and  foremost,  how  can 
 you  guys  even  get  set  up  with  Claude 
 Code?  For  me  personally,  I  like  to  use 
 Cursor.  You  will  see  here  there's 
 actually  a  Claude  Code  on  the  left  side. 
 There's  one  here  with  tabs  and  then  the 
 good  old  terminal.  Generally  speaking, 
 you'll  see  right  here  if  I  there's 
 plugins  for  Cursor  and  then  I  have  two 
 pretty  much  Claude  Codes,  although  it's 
 the  same  one,  but  I  think  it's  actually 
 a  matter  of  preference  where  let's  say 
 I'm  doing  some  coding  and  this  lives  on 
 the  left  side  where  I  can  actually  do 
 the  panel,  the  panel  view.  This  one  is 
 more  multi-agent  orchestration,  so  I  can 
 just  keep  opening  new  tabs  and  I  can  sit 
 here  and  just  have  multi-agents  do  a 
 bunch  of  stuff.  So,  this  one  creates  a 
 little  bit  more  orchestration  for 
 multi-agent  workflows.  And  then  the  good 
 old  terminal,  which  lives  everywhere, 
 right?  It's  on  your  computer.  The  other 
 thing  too,  if  you're  not  so  keen  using 
 an  actual  IDE  like  VS  Code  or  Cursor, 
 the  good  old  chat  app.  So,  there's  chat 
 Claude  Co-work,  which  is  kind  of  the 
 same  as  Claude  Code  except  it's  just 
 worded  a  little  differently,  but  it  can 
 actually  do  things  like  create  files. 
 And  then  there's  Claude  Code  right  here, 
 which  you'll  be  able  to  edit  files,  but 
 it's  in  this  interface  as  well.  So,  that 
 is  how  you  set  up  your  Claude  Code 
 instance.  What  we're  going  to  need  to  do 
 is  start  off  with  the  Claude  Code  fresh 
 chat.  We  have  a  list  of  leads,  which  you 
 can  see  right  here.  You  just  basically 
 want  to  create  a  empty  folder.  You  want 
 to  structure  that  folder  and  how  you 
 want  to  structure  like  leads,  campaigns, 
 copy.  It's  kind  of,  you  know,  no 
 different  than  your  computer  where  you 
 just  structure  in  specific  way  to  keep 
 it  nice  and  organized.  Let's  say  we  want 
 to  create  leads  folder  and  then  we  can 
 move  our  leads  into  there  and  then  just 
 say  move.  And  then  from  here,  we  will 
 also  install  Instantly  CLI,  which  is 
 very  easy.  I'm  actually  going  to  use 
 this  sidebar  here.  Install  Instantly  npm 
 install  -g  Instantly  CLI.  I  will  provide 
 you  the  API  key  here  shortly  once  you 
 install.  Let's  also  install  this  on  the 
 project  level  for  this  project.  [music] 
 And  then  you  notice  too,  I  went  bypass 
 permissions.  This  is  across  the  board.  I 
 like  to  go  straight  yolo  mode,  right? 
 With  bypassing  all  permissions,  but 
 you'll  have  ask  before  edits,  edits 
 automatically.  This  is  just  your  level 
 of  comfort.  Most  of  the  time  you  want  to 
 default  here,  but  if  you  want  to  go 
 straight  yolo,  sometimes  you  want  to 
 watch  it  because  it  could  fall  off  the 
 rails,  but  you  want  to  be  able  to  steer 
 your  AI  as  much  as  possible  to  have  good 
 prompting  and  good  outcomes.  going  to  go 
 ahead  and  send  it.  Firstly,  I'm  going  to 
 install  Instantly  CLI,  so  we  have  our 
 lead  list.  Let's  set  up  Instantly.  You 
 can  see  here  just  made  the  bash  command 
 of  npm  install  and  we  will  get  it 
 installed  and  then  we're  going  to  go  to 
 Instantly  and  you'll  just  go  to  your 
 workspace,  go  to  integrations,  API  keys, 
 and  then  we're  just  going  to  call  this 
 Claude  Code  Demo.  We're  going  to  give  it 
 all  scopes.  We're  going  to  hit  create 
 and  we'll  go  there.  And  then  we  say  both 
 installs  are  done.  The  package  is 
 Instantly  CLI  and  the  binary  is 
 Instantly.  So,  effectively,  what  this 
 does  is  it  allows  the  whole  Instantly 
 API,  which  I  believe  is  156  endpoints 
 and  it's  basically  everything  and 
 obviously  growing.  And  this  is  similar 
 to  the  MCP  server  where  you  can 
 effectively  tie  your  agent  to  an 
 external  source  that  has  an  API.  So, 
 their  API  is  like  create  campaign, 
 monitor  inbox,  literally  anything  on  the 
 platform.  Now,  the  agent  can  do.  The 
 difference  here  is  with  the  CLI  tool, 
 which  is  command  line  interface.  It's 
 able  to  do  very  simple  bash  or  terminal 
 commands  to  know  exactly  what  it's 
 looking  for  in  order  to  do  the  job.  So, 
 the  CLI  is  the  most  native  agentic  way, 
 which  is  through  the  terminal,  to 
 actually  get  the  job  done.  Whereas  for 
 us,  as  humans,  we  like  to  see  visually 
 pretty  things  like  click  mouse  and  drag 
 and  all  that  kind  of  stuff.  So,  now  we 
 have  both  installs  are  done.  Cool,  but 
 for  the  API  key,  this  is  not  usually 
 best  practice.  What  I  would  say  is 
 generate  an  API  key  and  if  it  gets 
 tokenized,  usually  want  to  cancel  it  or 
 rotate  it.  For  this  purpose,  we're  just 
 going  to  feed  into  there.  What  you  can 
 do  is  actually  connect  the  API  key 
 through  the  terminal  or  in  a,  what  do 
 you  call  it,  environment  file,  which  is 
 a  .env.  You  want  to  be  able  to  securely 
 store  your  your  credentials  with  that. 
 But  we've  authenticated  workspace  for 
 Tofu.  API  key  is  stored  right  here.  No, 
 that  CLI's  API  key,  the  flag  didn't  work 
 in  my  testing,  only  the  Instantly  API 
 key.  That's  really  interesting.  Does  it 
 work  then?  We  just  want  to  do  a  quick 
 check.  Okay,  we're  authenticated  and 
 good  to  go.  Now,  this  is  going  to  create 
 our  campaign  and  it's  actually  going  to 
 do  the  whole  thing  of  being  able  to 
 create  personalized  copy.  So,  we're 
 going  to  bring  up  our  lead  list.  You  can 
 see  here  this  is  just  a  CSV,  which  CSV 
 just  means  comma-separated  values.  So, 
 this  is  literally  what  a  CSV  looks  like 
 in  its  raw  form.  You  may  be  used  to  like 
 Google  Sheets  or  rows  and  columns  for  us 
 to  be  able  to  internalize  and  interpret 
 the  data.  So,  what  we're  going  to  say 
 here  is  I'm  going  to  use  Spokenly,  which 
 is  my  speech-to-text  dictation  tool, 
 using  the  Instantly  list.csv. 
 We  have  a  list  of  leads  where  we  are 
 trying  to  set  up  a  campaign  using 
 Instantly.  And  the  thing  is  is  each  and 
 every  person  has  a  unique  position,  a 
 unique  company,  and  a  unique  signal. 
 What  I  want  to  do  is  to  have  you  go 
 through  each  and  every  person  by  using  a 
 Python  library  called  Polars.  So,  what  I 
 want  you  to  do  is  to  set  up  a  virtual 
 environment.  What  I'm  doing  here  is  I'm 
 actually  containerizing  it  and  then  I'm 
 going  to  use  what  you  call  Polars. 
 There's  two  types,  Polars  and  Pandas. 
 And  for  those  non-techies,  really  it 
 just  makes  the  agent  to  very  quickly  rip 
 through  a  CSV,  more  rows  and  columns 
 than  you  can  even  imagine,  literally  in 
 a  matter  of  seconds.  So,  we're  just 
 going  to  go  with  that.  And  what  I  want 
 to  do  is  have  you  analyze  this  CSV.  I 
 want  you  to  one  by  one  research  each 
 company  by  launching  parallel  agents  in 
 the  background  so  we  can  get  this  done 
 as  fast  as  possible.  Then  I  want  you  to 
 understand  what  the  person  does  in  each 
 and  every  company,  especially  the  role 
 at  that  company.  And  then  what  we  want 
 to  do  is  we  want  to  send  them  a  message 
 basically  offering  our  services.  Here's 
 the  unique  thing  though,  is  we  need  to 
 have  our  campaign  specific  to  them.  It 
 needs  to  pique  their  curiosity  and  it 
 needs  to  lead  with  value  in  such  a  way 
 that  makes  them  pause  and  think  about 
 how did  they  do  that  or  how  did  they 
 know  that  information  and  creates  for 
 them  to  really  think  about  this  email 
 came  to  me  and  they're  not  quite  sure 
 how  it  was  done,  but  they  appreciate  the 
 effort  and  the  research  that  was  done  in 
 order  to  actually  reach  out  to  them. 
 Everybody  in  this  list,  pretty  much 
 everybody  in  this  world,  knows  what  a 
 cold  outreach  is  and  pretty  much 
 everybody  sometimes  ignores  it,  but  it's 
 the  only  good  ones  where  it  feels  right 
 and  it  feels  like  it  was  actually 
 written  to  them  is  the  ones  that  will 
 actually  do  something.  On  another  note, 
 there  are  three  things  that  these 
 prospects  will  do,  which  is  with  smart 
 buyers,  is  that  they  will  either  not 
 respond,  which  will  be  a  large  pool  of 
 them.  They  will  respond  with  yes  or  no, 
 or  they  will  actually  research.  They 
 will  not  respond,  but  they'll  research 
 us  at  top  of  funnel  or  whoever  the 
 prospect  is  and  they  will  self-serve, 
 self-educate,  and  then  take  action  from 
 there.  The  objective  here  is  to  simply 
 send  an  email  leading  with  value.  And  if 
 you  have  any  questions,  I  need  you  to 
 ask  me  what  that  means.  But  the 
 frameworks  of  a  cold  email  is  this.  The 
 first  line  is  absolutely  the  most  vital 
 piece  of  information  that  we  need  to 
 come  in  and  lead  with.  The  reason  for 
 that  is  because  the  first  line  is  what 
 buys  attention.  And  if  we  stop  them  in 
 their  tracks  and  we  actually  catch  them 
 on  the  first  line  by  generating  or 
 earning  1  to  3  seconds  of  attention. 
 Then  we  are  earning  more  attention  by 
 actually  then  finishing  the  email.  Each 
 email  needs  to  be  around  or  less  than 
 100  words.  It  needs  to  be  optimized  with 
 new  lines  that  are  optimized  for  mobile 
 devices  because  a  lot  of  people  in  this 
 world  read  their  emails  on  a  mobile 
 device.  If  it's  anything  else  other  than 
 a  mobile,  that's  okay,  too.  But  these 
 emails  need  to  be  very  simple  to  read, 
 very  easy  to  read,  and  it  needs  to  be 
 quick.  The  frameworks  are  is  this.  There 
 needs  to  be  a  very  simple  greeting 
 because  that's  what  humans  do.  The  first 
 line  needs  to  be  so  specific  to  them  and 
 direct  and  something  that  you  notice 
 that's  interesting  without  any  small 
 talk.  Never  say,  "I  hope  this  email 
 finds  you  well."  Never  say,  "Oh,  I  see 
 that  your  your  LinkedIn  profile's 
 amazing."  Or  I  see  a  lot  of  your  great 
 work.  That  doesn't  mean  anything  in  this 
 scenario.  It  needs  to  be  specific  to 
 them  to  know  that  it  is  relevant.  As 
 another  scenario,  if  we  were  in  an 
 elevator  in  person  and  I  did  not  know  a 
 particular  stranger,  yet  that  stranger 
 was  wearing  some  clothes  that  perhaps 
 had  a  stain  on  it  and  I  see  that  they 
 have  it.  Well,  if  I  were  to  have  a  stain 
 remover  pen  in  my  pocket,  for  example,  I 
 might  actually  say,  "Hey,  I  noticed  that 
 stain  on  your  shirt.  I  actually  have  a 
 stain  remover  in  my  pocket."  And  ask 
 them  if  they  would  need  it  or  if  that 
 would  help  or  would  they  would  like  to 
 try  it.  The  frameworks  for  emails  is  no 
 different.  It  is  very  direct,  it's  very 
 relevant,  and  it  shows  value  that  they 
 have  a  problem  or  a  situation  for  them 
 at  which  we  know  how  to  improve.  There 
 are  only  three  reasons  why  anybody  in 
 B2B  transact  with  another  B2B  company, 
 and  that  is  this.  Number  one,  they 
 either  need  to  save  time.  Number  two, 
 they  need  to  save  money.  Or  three,  they 
 need  to  make  more  money.  It's  either  one 
 of  those  three  or  all  three.  Otherwise, 
 B2B  does  not  exist.  So  I  just  want  you 
 to  generate  copy  with  that  in  mind  and 
 know  that  each  and  every  prospect  needs 
 to  be  earned  in  terms  of  attention.  And 
 what  we're  trying  to  do  here  is  not  go 
 cold  to  close.  We're  trying  to  go  from 
 cold  outreach  to  warm  intent  and  peak 
 curiosity.  I  need  you  to  confirm  with  me 
 that  you  understand  before  you  actually 
 go  and  do  something.  Then  I  want  you  to 
 tell  me  your  plan  on  how  you're  going  to 
 do  that.  And  then  I  will  approve  or 
 modify  your  plan  so  that  way  we  can  be 
 aligned  the  whole  time.  So  that's  the 
 fastest  way  you  can  actually  output 
 information  is  just  by  talking.  And  it 
 saves  your  keyboard,  saves  your  fingers. 
 All  right,  we're  all  done  here.  So  let's 
 review  what  it  said  here.  Before  I  touch 
 anything,  let  me  confirm  what  I  heard 
 and  lay  out  a  plan.  There  are  a  few 
 things  that  I  need  clarified  before  I 
 start  because  some  choices  have  real 
 cost  comp  implications  with  that  scale. 
 Cold  to  warm,  not  cold  to  close.  Earn  a 
 reply  by  peaking  curiosity  through 
 research  and  the  prospect  can  feel  the 
 wait,  did  they  know  how  did  they  do  that 
 reaction  copy  rules.  Under  100  rules,  so 
 that  reiterates  everything  that  I  said. 
 Work  for  you  describe,  set  up  a  Python 
 VNV  with  Polars.  Yes,  that's  right.  Load 
 and  analyze  the  CSV.  All  right,  we  have 
 1,000  leads.  Research  each  company  plus 
 role  in  parallel  we  using  background 
 agents,  right?  So  that  way  doesn't  go 
 just  one  agent  and  we  sit  here  forever 
 or  I  go  do  something  cuz  I'm  trying  to 
 get  this  done  with  good  time  here. 
 Generate  a  unique  cold  email  or  email 
 per  lead  grounded  in  that  research. 
 Eventually  feed  into  instantly  campaign. 
 That's  exactly  right.  Things  you  need 
 for  me.  Scale,  there  are  1,000  leads. 
 Researching  1,000  leads  with  additional 
 agents  is  expensive  in  both  time  and 
 tokens.  Probably  hours  of  wall  time  and 
 significant  cost.  Run  a  small  highlight 
 first.  Okay,  run  the  full  1,000.  Pick  a 
 subset.  My  strong  recommendation  is  a 
 pilot  first.  For  this  use  case,  I  think 
 we're  going  to  do  that  for  I'd  say 
 probably  the  first  20  cuz  we  want  to  get 
 a  sample.  We  want  to  see  what  that  looks 
 like.  Our  services,  what  Top  of  Funnel 
 actually  offers  these.  I  can't  leave 
 with  value  if  I  don't  know  the  value. 
 Oh,  that's  hilarious.  The  Claude  MD 
 doesn't  specify  the  offer.  Okay.  All 
 right,  see  a  signal.  All  right,  it  has  a 
 name.  Cool.  While  I'm  reading  this,  I'm 
 actually  going  to  click  on  this  and  I'm 
 going  to  use  the  speech  and  I'm  going  to 
 talk  to  the  agent  as  I'm  reading  it 
 because  then  it  will  transcribe.  This 
 entire  plan  sounds  good  based  on 
 everything  that  you  have  outlined.  Where 
 you  say  it  says  the  things  I  need  you  to 
 clarify  before  I  plan  accordingly  is 
 scale.  I  understand  the  implications  of 
 what  you're  saying.  Therefore,  I  agree 
 with  you.  Let's  run  20  emails  as  a  pilot 
 to  make  sure  that  the  frameworks  is  good 
 before  you  run  at  scale.  So  that  way 
 while  you're  working  to  enrich  that  in 
 the  background,  I  can  go  do  something 
 else  and  I  have  to  sit  here  and  wait  for 
 as  long  as  you  say.  I  definitely 
 recommend  to  run  parallel  agents  so  that 
 way  it's  actually  generating  at  the  same 
 time  and  that  we're  maximizing  our 
 efficiency.  With  that  said,  you  said  our 
 services,  that  is  a  great  callout.  What 
 I  want  you  to  do  first  and  foremost,  so 
 I  don't  have  to  explain  myself,  is  to 
 actually  just  look  up  Top  of  Funnel.com 
 and  I  want  you  to  understand  what  we  do 
 and  then  I  want  you  to  pick  the  best 
 approach  on  how  our  services  and  our 
 offer  is  relevant  to  these  companies. 
 The  signal.  Your  CSV  doesn't  have  a 
 signal  column.  It  has  a  name,  company 
 title.  When  you  say  each  person  has  a 
 unique  signal,  I'm  assuming  the  signal 
 is  something  that  I  need  to  discover 
 during  research.  Recent  funding  round, 
 new  hire,  product  launch.  Exactly  right. 
 Confirm  that's  right  and  tell  me  signal. 
 This  is  perfect.  When  you  say  output 
 destination,  I  want  you  to  append  it  to 
 the  same  CSV  so  that  way  we  can  review 
 it.  And  then  at  the  same  20  emails,  I 
 want  you  to  create  a  markdown  file  of 
 those  so  I  can  easily  review  it  without 
 having  to  scroll  through  a  CSV  file. 
 Sequence  length.  I  love  that.  That's 
 great.  We  need  to  do  a  multi-step.  So 
 let's  do  a  three  email  sequence  and  then 
 let's  do  the  first  email  obviously  goes 
 out.  The  second  email  will  go  out  after 
 3  days  and  then  the  third  email  will  go 
 out  after  7  days.  From  here,  you  will 
 see  that  it  will  start  cooking  and  we 
 should  see  copy  here  in  a  moment.  All 
 right,  so  now  that  Claude  code  has  ran 
 for  about  20  minutes  now,  we  are  all 
 done.  So  let's  review  what  it  did  and 
 let's  review  the  copy  and  let's  see 
 where  we  land.  So  from  here,  you  can  see 
 that  I  said  everything  here.  It  says  all 
 clear.  Let  me  load  a  couple  of  tools 
 I'll  need  and  I'll  start  by 
 understanding  what  Top  of  Funnel 
 actually  does.  So  I  instructed  Claude 
 code  obviously  to  look  into  what  we  do 
 and  I  didn't  even  really  give  it  a  whole 
 lot  of  context  other  than  just  our 
 website.  So  we'll  see  if  it  actually 
 comes  through.  I  don't  know.  This  is 
 part  of  the  demo.  But  you  can  see  here  I 
 can  only  improve  by  providing  as  much 
 context  as  possible  in  order  to  have  it 
 actually  accurate.  So  it'll  make  it  to 
 do  list,  which  is  really  cool.  It 
 actually  will  sit  there  and  sequentially 
 go  through  all  the  things.  And  in  fact, 
 a  lot  of  times  it'll  actually  launch 
 background  agents  in  parallel  so  it 
 keeps  this  context  window  nice  and 
 clean.  One  last  thing  before  we  dive  in, 
 you'll  actually  see  these  little  like 
 blurbs  of  insights.  That's  relatively 
 new.  It's  been  out  for  a  little  while 
 now,  but  I  wouldn't  shy  away  from  those. 
 Those  are  good  learning  opportunities. 
 So  you  see  it  update  to  do.  So  it's 
 going  through  everything  here.  The  site 
 talks  about  a  lot  of  stuff.  These  are 
 really  where  it's  making  terminal 
 commands.  So  it's  using  Firecrawl  as  a 
 scraper  to  understand  more  context  about 
 our  website.  It  says  got  it.  It's 
 basically  talking  to  itself.  So  it 
 understands  more  about  Top  of  Funnel. 
 Then  it's  setting  up  a  Python  virtual 
 environment  and  install  Polars.  Pilot  20 
 selected  stratified  across  sales, 
 marketing,  data,  ops,  executive,  and 
 engineering  buckets.  Top  decision  makers 
 scored  per  bucket.  Let  me  see  all  20  so 
 I  have  them  in  front  of  me  before 
 dispatching  research  engine.  So  you  can 
 pretty  much  get  the  gist  of  it.  It  goes 
 through  a  bunch  of  stuff  here  and  then 
 it  will  come  out  with  a  summary,  which 
 we  will  scroll  to.  And  it'll  say  pilot 
 is  complete.  Here's  the  punch  list  of 
 what  landed  and  where.  Output's  ready 
 for  review.  So  we  have  a  markdown  file, 
 which  is  a  human-readable  file.  So  if  we 
 just  click  on  this,  you  can  see  this 
 looks  readable,  but  I'm  going  to  show 
 you  something  that  actually  makes  it  a 
 lot  easier,  which  this  is  why  I  like 
 having  an  environment.  I'm  going  to  hit 
 shift  command  V  and  that's  actually 
 going  to  do  a  preview  mode.  And  you  will 
 be  able  to  have  this  render.  So  it 
 selected  a  bunch  of  randoms  based  on 
 segments  and  what  have  you.  And  then  we 
 also  have  leads  pilot  20  enriched.csv. 
 The  original  lead  columns  plus  research 
 fields  and  all  six  email  columns  are  all 
 good  to  go.  And  then  we  have  pilot 
 emails.json.  When  you're  working  in  a 
 coding  environment  such  as  this,  a  lot 
 of  times  humans  are  used  to  just  CSVs. 
 So  we  could  have  this  enriched  in  a  CSV 
 just  like  this,  which  to  humans  you're 
 just  be  like,  "Wait,  what?"  And  then  a 
 JSON  is  actually  structured  a  little  bit 
 differently.  So  it  actually  makes  more 
 sense  from  a  structural  data  standpoint. 
 It is  a  lot  more  scalable.  So  what  we 
 want  to  do  here  is  uh  we're  just  going 
 to  read  this  markdown  file  and  kind  of 
 go  through  some  of  the  example  copies  so 
 that  way  we  can  preview  it.  We  can 
 iterate,  of  course,  and  do  whatever  we 
 want.  Uh  this  is  obviously  a  one-shot. 
 So  sometimes  we  might  want  to  review  the 
 sample  copy  to  actually  refine.  That's 
 why  I  did  the  sample  copy  here  before 
 doing  all  1,000.  All  16  emails,  20 
 leads,  and  three  steps.  Perfect. 
 Automated  checks.  Word  count.  Everybody 
 lands  at  80  to  100  words.  Ban  phrases. 
 So  it  actually  did  that  for  me.  No  hope 
 this  email  finds  you  well,  LinkedIn 
 flattery,  hard  CTAs,  corporate,  circle 
 back,  deep  dive,  etc.  We  have  a  soft 
 call  to  action.  Every  email  ends  with  a 
 recognizable  low-friction  ask.  It  should 
 be  a  no-brainer.  Subject  line.  All  under 
 60  characters.  So  I  actually  didn't  even 
 say  that,  but  that's  great  that  it  knows 
 it  because  you  definitely  want  to  do  it. 
 Under  60  characters  is  a  good  target, 
 but  quite  honestly,  if  you  can  even  have 
 it  less  than  33  characters  because 
 usually  it's  pretty  subjective,  but  I 
 want  to  say  it's  34,  where  it  will 
 actually  become  truncated,  where  if 
 you're  looking  on  a  phone,  right?  Your 
 subject  line  is  actually  going  to  be  cut 
 off.  So,  that's  why  everybody  says  quick 
 question,  cuz  it  actually  probably  does 
 all  the  time.  But,  try  to  keep  your 
 subject  lines  very  short  and  punchy. 
 Quality  breakdown,  worth  flagging  before 
 you  read.  You  want  to  see  here  how  I 
 broke  it  down,  inferred  signals,  right? 
 So,  the  AI  really  did  some  research  here 
 and  inferred  with  different  signals 
 across  it  on  how  it  was  able  to 
 research.  Again,  this  is  the  time-saving 
 aspect  of  like,  I  don't  need  to  sit  here 
 and  research  and  reason  on  why  I  want  to 
 reach  out  to  this  person,  right?  And  to 
 make  a  good  grabbing  email.  We  have  some 
 examples  here,  sequence  shape,  what 
 changed  in  the  working  tree.  So,  you  can 
 see  here  this  is  Margaret,  saw  Lattice 
 is  taking  the  AI  agent  platform  on  the 
 road  with  LatticeVerse  2026,  a  real  bet 
 on  people  and  AI  working  together.  I 
 mean,  that's  relevant,  that's  okay.  You 
 know  Margaret.  You  know  what?  Let's  send 
 it  anyway,  right?  Curious  thing  on  the 
 sales  side,  from  director  job  spec,  your 
 AEs  are  running  full  cycle,  both  inbound 
 and  outbound.  That's  expensive  closer 
 time  spent  on  prospecting  and 
 sequencing,  SDR  output.  Another  thing 
 that  I  recommend  is  to  make  sure  that 
 the  AI  does  not  put  M  dashes  on  AI,  cuz 
 that's  another  AI  slop  that  we  all  know. 
 And  we  go  to  the  call  to  action.  This  is 
 again  proof.  We  build  grounded  outbound 
 systems  on  Claytann  Instantly  that  hand 
 AEs  warm  meetings  without  adding  head 
 count.  20.8%  reply  rates  in  our  last 
 SaaS  run.  This  is  actually  true,  so  it 
 probably  scraped  our  website.  So,  what  I 
 would  do  is  actually  take  out  the  M  dash 
 and  then  this  is  one  of  those  like  too 
 good  to  be  true  scenarios,  cuz  that's 
 really  nice,  but  let's  be  real,  it's 
 usually  like  1  to  3%.  Anything  north  of 
 that,  you're  like  really  good.  Anything 
 less  than  1%,  something  is  off.  The  goal 
 here  is  look  at  the  meat  of  an  email.  We 
 have  the  hook,  that's  relevant.  We  have 
 the  body  about  offer  and  picking 
 curiosity  about  hey,  I'm  just  curious, 
 you  know,  cuz  it's  usually  soft.  And 
 then  let's  go  to  another  lead  here.  So, 
 Mary,  hi  Mary,  saw  Segment  shipped 
 entity-based  linked  audiences  on  March 
 26th.  Scoping  audiences  to  accounts  and 
 households  is  a  real  unlock  for  partner 
 ecosystem.  The  story  is  great,  the  hard 
 part  is  getting  in  front  of  the  right 
 partner  GTM  leads  at  the  right  accounts 
 without  blasting  Twilio  domain.  So, 
 that's  kind  of  good.  We  built  grounded 
 partner  aware  systems,  all  right.  And 
 the  thing  here  is  it  scraped  our  site.  I 
 didn't  really  tell  the  agent  what  we  do, 
 delivery-optimized  last  SaaS  run.  The 
 big  takeaway  here  is  really  the 
 frameworks  don't  change.  You  have 
 literally  one  opportunity.  You  want  to 
 be  able  to  grab  their  attention  and  then 
 buy  more  attention  by  showing  the  meat 
 and  potatoes.  You  can  see  the  formatting 
 is  good,  it's  very  quick,  should  take  no 
 more  than  maybe  5  seconds  to  skim  over 
 and  you'll  be  able  to  like  know 
 instantly  what  the  next  move  is.  So, 
 from  here  we're  going  to  say,  okay, 
 great,  these  samples  look  good  by  first 
 pass.  Let's  go  ahead  and  create 
 inside  of  Instantly  using  the  Instantly 
 CLI.  Please  make  sure  you  title  it  in 
 such  a  way  with  the  current  date  and 
 title  it  in  such  a  way  that  we  can  know 
 exactly  what  campaign  it  is.  From  there, 
 I  want  you  to  load  the  leads  and  I  want 
 you  to  load  the  copy  that  you're  already 
 generated  and  let's  take  a  look  here 
 before  we  run  anything  at  scale  and  then 
 I  will  tell  you  to  run  at  scale.  So, 
 what  this  is  actually  going  to  do  is  use 
 the  Instantly  CLI  and  it's  literally 
 going  to  create  the  copy  or  create  the 
 copy,  it's  going  to  create  the  campaigns 
 and  then  we  will  actually  go  into 
 Instantly  and  and  see  what  we  have  here. 
 All  right,  so  we  can  see  here  campaign 
 created,  we  got  the  ID  there,  status 
 zero,  which  means  paused,  settings 
 landing,  text  only,  no  open  tracking, 
 stop  on  reply.  These  are  all  defaults 
 that  I  put  into  the  Instantly  CLI,  cuz 
 it's  best  practices.  And  from  there, 
 sequence  has  delays,  perfect.  All  20 
 leads  uploaded,  zero  duplicates,  zero 
 invalid,  that's  good  stuff.  Campaign 
 created  gives  us  the  summary  and  then  we 
 have  everything  here.  We  have  email  one 
 subject,  email  one  body.  Let's  go  ahead 
 and  see  what  we're  looking  at.  We  have 
 the  outbound  test  right  here.  We  have 
 outbound  body,  email  two,  email  two 
 subject  and  body.  So,  it  already  created 
 the  actual  text  here.  Let's  hit  preview, 
 make  sure  it  works.  There  it  is.  All 
 right,  so  we  have  nice  proper  spacing 
 and  we're  going  through  here.  If  I  were 
 to  select  another  lead,  we  can  go 
 through  hi  Margaret  and  then  we  can  go 
 through  Natasha,  good  formatting  and 
 everything,  all  good  to  go.  So,  this 
 right  here  is  what  emails  should  look 
 like,  because  everything  in  the  leads 
 category,  we  actually  have  good  data 
 here  and  then  you  can  see  in  the  email 
 bodies  and  everything,  that  is,  in  my 
 opinion,  what  personalized  email  with 
 cloud  code  looks  today.  Now,  you've  got 
 the  system  for  writing  personalized 
 emails  at  scale,  but  the  system  only 
 works  if  the  emails  you're  sending  are 
 actually  converting.  So,  click  this 
 video  here  because  when  we  break  down 
 the  new  rules  of  cold  email  in  2026, 
 what's  working  now,  what's  dead  and  the 
 exact  [music]  framework  we  use  to  write 
 cold  emails  that  fill  up  your  calendar. 
 If  you're  already  sending  volume,  this 
 is  what  turns  it  into  booked  meetings. 
 Thanks  for  watching  and  I'll  see  you  in 
 the  next  one.