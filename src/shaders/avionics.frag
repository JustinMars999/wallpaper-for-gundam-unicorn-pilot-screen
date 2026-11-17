// SPDX-License-Identifier: GPL-3.0-only
const vec3 paper=vec3(.82,.88,.84);
const vec3 phosphor=vec3(.48,.85,.67);
const vec3 ice=vec3(.43,.75,.82);
const vec3 amber=vec3(.98,.72,.35);
const vec3 dimInk=vec3(.24,.36,.34);
float avNumber(vec2 p,vec2 origin,vec2 glyph,float val,int count){
  vec2 n=(p-origin)/glyph;
  if(n.x<0.||n.y<0.||n.x>=float(count)||n.y>=1.)return 0.;
  int i=count-1-int(floor(n.x));
  float k=mod(floor(abs(val)/pow(10.,float(i))),10.);
  float footprint=max(fwidth(p.x)*48./glyph.x,fwidth(p.y)*79./glyph.y);
  return textureLod(panelTex,vec2((k*48.+fract(n.x)*48.)/4096.,(720.+n.y*79.)/800.),clamp(log2(max(1.,footprint)),0.,3.)).r;
}
float signGlyph(vec2 p,vec2 origin,vec2 size,float v){
  vec2 n=(p-origin)/size;
  if(any(lessThan(n,vec2(0.)))||any(greaterThan(n,vec2(1.))))return 0.;
  return texture(panelTex,vec2(((v<0.?11.:10.)*48.+n.x*48.)/4096.,(720.+n.y*79.)/800.)).r;
}
float strokeCircle(vec2 p,float r,float width,float aa){
  return 1.-smoothstep(width-aa,width+aa,abs(length(p)-r));
}
bool box(vec2 p,vec2 a,vec2 b){return all(greaterThanEqual(p,a))&&all(lessThanEqual(p,b));}
vec3 tape(vec3 col,vec2 uv,float val,float stepSize,bool left,float aa){
  float orient=left?-1.:1.,edge=left?.227:.773;
  float current=floor(val/stepSize);
  col+=dimInk*line2(uv,vec2(edge,.256),vec2(edge,.746),.0012,aa);
  for(int i=-3;i<=3;i++){
    float reading=(current+float(i))*stepSize;
    float y=.504+((val-reading)/stepSize)*.086;
    if(y>.266&&y<.741){
      col+=paper*.65*line2(uv,vec2(edge,y),vec2(edge+orient*.023,y),.0017,aa);
      col+=paper*.64*avNumber(uv,vec2(left?.092:.812,y-.025),vec2(.021,.050),reading,left?4:3);
    }
    float yy=y+.043;
    if(yy>.266&&yy<.741)col+=dimInk*line2(uv,vec2(edge,yy),vec2(edge+orient*.011,yy),.0012,aa);
  }
  float x0=left?.024:.811,x1=left?.189:.977;
  if(box(uv,vec2(x0,.440),vec2(x1,.565))){
    col=vec3(.007,.022,.027);
    float border=min(min(uv.y-.440,.565-uv.y),min(uv.x-x0,x1-uv.x)*2.65);
    col=mix(col,phosphor*.9,1.-smoothstep(.001,.004,border));
    col+=phosphor*avNumber(uv,vec2(left?.048:.836,.445),vec2(left?.030:.035,.116),val,left?4:3);
  }
  float notch=left?x1:x0;
  col+=phosphor*line2(uv,vec2(notch,.480),vec2(notch-orient*.013,.504),.0013,aa);
  col+=phosphor*line2(uv,vec2(notch-orient*.013,.504),vec2(notch,.529),.0013,aa);
  return col;
}
vec3 primaryDisplay(vec3 base,vec2 uv,float roll,float pitch,float power,float heading,float aa){
  float bank=.123-roll*.98, alt=408.2+2.65*sin(phase-.18)+1.18*sin(2.*phase+.55);
  float rate=34.907*(2.65*cos(phase-.18)+2.36*cos(2.*phase+.55));
  float speed=7666.-4.7*(alt-408.2)+6.*(power-.5);
  if(box(uv,vec2(.259,.246),vec2(.741,.787))){
    vec2 z=(uv-vec2(.50,.515))*vec2(2.70,1.);
    vec2 b=rot(-bank)*z; b.y+=pitch*1.37;
    float horizon=smoothstep(-aa,aa,b.y);
    vec3 sky=mix(vec3(.078,.147,.224),vec3(.163,.284,.378),1.-min(1.,abs(b.y)*2.5));
    vec3 ground=mix(vec3(.195,.140,.100),vec3(.287,.211,.136),1.-min(1.,abs(b.y)*2.9));
    base=mix(sky,ground,horizon);
    base=mix(base,paper*.88,1.-smoothstep(.0012,.0012+aa,abs(b.y)));
    for(int i=-4;i<=4;i++){
      if(i==0)continue;
      float y=float(i)*.054, len=abs(i)%2==0?.189:.095;
      float h=line2(b,vec2(-len,y),vec2(-.037,y),.0022,aa)+line2(b,vec2(.037,y),vec2(len,y),.0022,aa);
      if(abs(i)%2==0){
        h+=line2(b,vec2(-len,y),vec2(-len,y-.014*sign(y)),.0021,aa);
        h+=line2(b,vec2(len,y),vec2(len,y-.014*sign(y)),.0021,aa);
      }
      base=mix(base,paper*.87,clamp(h,0.,1.));
    }
    vec2 c=vec2(0.,.035);
    for(int i=-3;i<=3;i++){
      float a=float(i)*.174533;
      vec2 dir=vec2(sin(a),-cos(a));
      float radius=.254;
      base+=paper*.77*line2(z,c+dir*radius,c+dir*(radius-(i%3==0?.024:.012)),.0024,aa);
    }
    vec2 car=c+vec2(sin(-bank),-cos(bank))*.217;
    float pointer=line2(z,car+vec2(-.014,.012),car+vec2(0.,-.007),.0026,aa)+line2(z,car+vec2(0.,-.007),car+vec2(.014,.012),.0026,aa);
    base=mix(base,amber,clamp(pointer,0.,1.));
    for(int i=-1;i<=1;i+=2){
      float s=float(i);
      float shadow=line2(z,vec2(s*.248,0.),vec2(s*.084,0.),.009,aa)+line2(z,vec2(s*.083,-.001),vec2(s*.083,.025),.0085,aa);
      base=mix(base,vec3(.020),clamp(shadow,0.,1.));
      float wing=line2(z,vec2(s*.248,0.),vec2(s*.084,0.),.004,aa)+line2(z,vec2(s*.084,-.001),vec2(s*.084,.025),.004,aa);
      base=mix(base,amber,clamp(wing,0.,1.));
    }
    base=mix(base,amber,1.-smoothstep(.005,.009,length(z)));
  }
  if(uv.x<.251)base=tape(base,uv,speed,10.,true,aa);
  if(uv.x>.749)base=tape(base,uv,alt,1.,false,aa);
  if(uv.y>.112&&uv.y<.244&&uv.x>.28&&uv.x<.72){
    for(int i=-4;i<=4;i++){
      float val=(floor(heading/5.)+float(i))*5.;
      float x=.5+(val-heading)*.012;
      if(x>.288&&x<.712){
        base+=dimInk*line2(uv,vec2(x,.208),vec2(x,.237),.0013,aa);
        if(mod(val,10.)<1.&&abs(x-.50)>.077)base+=paper*.70*avNumber(uv,vec2(x-.021,.159),vec2(.014,.046),val,3);
      }
    }
    if(box(uv,vec2(.454,.158),vec2(.546,.238))){
      base=vec3(.015,.033,.035);
      base+=phosphor*avNumber(uv,vec2(.460,.159),vec2(.027,.075),heading,3);
      float y=min(uv.y-.158,.238-uv.y);if(y<.003)base+=phosphor*.7;
    }
  }
  base+=paper*avNumber(uv,vec2(.124,.796),vec2(.032,.073),power*100.,2);
  base+=paper*signGlyph(uv,vec2(.841,.796),vec2(.025,.073),rate);
  base+=paper*avNumber(uv,vec2(.866,.796),vec2(.026,.073),abs(rate),3);
  return base;
}
vec3 navDisplay(vec3 base,vec2 uv,float heading,float aa){
  vec2 p=(uv-vec2(.50,.485))*vec2(1.00,1.);
  float dist=length(p), a=radians(heading);
  if(dist<.32){
    float sweep=mod(atan(p.x,-p.y)-phase*8.+2.*PI,2.*PI);
    base+=vec3(.016,.095,.065)*exp(-8.*sweep)*smoothstep(.04,.13,dist);
    for(int i=1;i<=3;i++)base+=dimInk*(i==3?.98:.62)*strokeCircle(p,float(i)*.098,.0019,aa);
    for(int i=0;i<24;i++){
      float b=float(i)*PI/12.-a;
      vec2 dir=vec2(sin(b),-cos(b));
      base+=paper*.63*line2(p,dir*.295,dir*(i%3==0?.265:.283),.00165,aa);
    }
    vec2 partner=vec2(.140*cos(phase+.54)-.027*sin(phase*2.+.9),-.167-.035*cos(phase-1.06));
    vec2 m=p-partner;
    float shape=abs(m.x)+abs(m.y);
    base+=phosphor*(1.-smoothstep(.001,.003+aa,abs(shape-.024)));
    base+=phosphor*line2(m,vec2(-.002,-.021),vec2(-.036,-.061),.0026,aa);
    base+=phosphor*avNumber(m,vec2(.024,-.019),vec2(.028,.046),1.,2);
    for(int s=-1;s<=1;s+=2){
      float side=float(s);
      base+=paper*line2(p,vec2(0.,-.026),vec2(side*.038,.015),.0032,aa);
      base+=paper*line2(p,vec2(side*.038,.015),vec2(0.,.005),.0028,aa);
    }
    vec2 route=rot(-.33-.19*sin(phase))*p;
    if(abs(route.x-.11)<.002&&route.y>-.28&&route.y<.26&&mod(route.y+.6,.044)<.025)base+=ice*.49;
  }
  return base;
}
vec3 instrument(int i,vec2 uv,float roll,float pitch,float power,float ctlR,float ctlL){
  float off=i==0?0.:1536.+float(i-1)*640.,wide=i==0?1536.:640.;
  vec3 base=texture(panelTex,vec2((off+clamp(uv.x,.001,.999)*wide)/4096.,clamp(uv.y,.001,.999)*720./800.)).rgb;
  float aa=max(.00085,.62*fwidth(uv.y));
  float heading=73.4+7.4*sin(phase-.31)+3.9*sin(2.*phase+.91);
  if(i==0)base=primaryDisplay(base,uv,roll,pitch,power,heading,aa);
  else if(i==1)base=navDisplay(base,uv,heading,aa);
  else if(i==2){
    vec2 pos=vec2(.500+.215*ctlR,.417-.129*ctlL);
    if(box(uv,vec2(.094,.225),vec2(.9,.609))){
      base+=phosphor*line2(uv,pos-vec2(.039,0.),pos+vec2(.039,0.),.003,aa);
      base+=phosphor*line2(uv,pos-vec2(0.,.033),pos+vec2(0.,.033),.003,aa);
      base+=phosphor*.85*strokeCircle(uv-pos,.020,.0025,aa);
      base+=dimInk*line2(uv,vec2(.50,.417),pos,.0017,aa);
    }
    float pitchDeg=-(pitch*165.),bankDeg=degrees(.123-roll*.98);
    base+=phosphor*signGlyph(uv,vec2(.052,.749),vec2(.060,.102),abs(pitchDeg)<1.?0.:pitchDeg);
    base+=paper*avNumber(uv,vec2(.114,.749),vec2(.069,.102),abs(pitchDeg),2);
    base+=phosphor*signGlyph(uv,vec2(.547,.749),vec2(.060,.102),bankDeg);
    base+=paper*avNumber(uv,vec2(.607,.749),vec2(.069,.102),abs(bankDeg),2);
  }else if(i==3){
    for(int j=0;j<2;j++){
      vec2 c=vec2((177.+286.*float(j))/640.,294./720.);vec2 p=uv-c;
      float fraction=power+(j==0?-.36:.36)*roll;
      float a=radians(135.+270.*fraction);
      vec2 dir=vec2(cos(a)*101./640.,sin(a)*111./720.);
      base+=amber*line2(p,dir*.54,dir*.97,.0045,aa);
      base+=paper*avNumber(uv,c-vec2(.063,.050),vec2(.062,.108),fraction*100.,2);
    }
    for(int j=0;j<22;j++){
      vec2 p=(uv-vec2(.085+float(j)*.039,.813))/vec2(.013,.011);
      float cell=1.-smoothstep(.82,1.,max(abs(p.x),abs(p.y)));
      base+=(j<int(10.+power*9.)?phosphor*.83:dimInk*.47)*cell;
    }
  }else{
    float light=.83+.17*sin(phase*4.);
    base+=vec3(.028,.066,.044)*light*(1.-smoothstep(.012,.017,length(uv-vec2(.93,.163))));
  }
  // Recessed, antireflective glass with a restrained off-axis reflection from the planet.
  float glass=.915+.065*(1.-smoothstep(.25,.74,distance(uv,vec2(.45,.41))));
  vec3 reflection=vec3(.006,.011,.017)*(.6+.4*uv.y);
  return clamp(base*glass+reflection,0.,1.);
}
