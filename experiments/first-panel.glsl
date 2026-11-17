// SPDX-License-Identifier: GPL-3.0-only
vec3 digits(vec2 st,vec2 origin,vec2 glyph,float value,int count){
  vec2 p=(st-origin)/glyph;
  if(p.x<0.||p.y<0.||p.x>=float(count)||p.y>=1.)return vec3(0.);
  int position=count-1-int(floor(p.x));
  float digit=mod(floor(abs(value)/pow(10.,float(position))),10.);
  return texture(panelTex,vec2((digit*48.+fract(p.x)*48.)/4096.,(720.+p.y*79.)/800.)).rgb;
}
vec3 instrument(int index,vec2 uv,float roll,float pitch,float power,float controlR,float controlL){
  float off=index==0?0.:1536.+float(index-1)*640.;
  float wide=index==0?1536.:640.;
  vec3 base=texture(panelTex,vec2((off+clamp(uv.x,.001,.999)*wide)/4096.,clamp(uv.y,.001,.999)*720./800.)).rgb;
  float aa=max(1.0/resolution.y,.00065);
  if(index==0){
    // The FD linework behind the suit was measured directly from the supplied menu frames.
    float n=(.5-.5*cos(phase+.45))*63.;
    vec3 old=mix(bankSample(floor(n),uv),bankSample(min(floor(n)+1.,63.),uv),fract(n));
    float periphery=.29+.71*smoothstep(.12,.29,abs(uv.x-.5));
    base+=periphery*(old.r*vec3(.25,.12,.24)+old.b*vec3(.055,.030,.065))+old.g*vec3(.012,.017,.044);
    float scan=.51+.36*sin(2.*phase-.30);
    float band=exp(-sq((uv.y-scan)/.051));
    base+=base*band*.18;
    for(int i=0;i<2;i++){
      float y=(229.+49.*float(i))/720., x2=.140+.056*(.55+.44*(i==0?controlL:controlR));
      base+=azure*line2(uv,vec2(.126,y),vec2(x2,y),.003,aa)*.75;
    }
    base+=digits(uv,vec2(.749,.812),vec2(.020,.054),92.+power*6.,2)*.76;
    float wave=.53+.03*sin(39.*uv.x-phase*6.)+.018*cos(87.*uv.x+phase*4.);
    if(uv.x>.728&&uv.x<.957)base+=azure*exp(-sq((uv.y-wave)/.0026))*.49;
  }else if(index==1){
    vec2 center=vec2(.5,340./720.);
    vec2 p=(uv-center)*vec2(640./720.,1.);
    p=rot(-roll)*p-vec2(0.,pitch*.35);
    float lim=1.-smoothstep(.178,.19,length(p));
    float l=line2(p,vec2(-.172,0.),vec2(-.033,0.),.0028,aa)+line2(p,vec2(.033,0.),vec2(.172,0.),.0028,aa);
    for(int i=-2;i<=2;i++){
      if(i==0)continue;
      float y=float(i)*.034, ln=abs(i)==1?.064:.041;
      l+=line2(p,vec2(-ln,y),vec2(ln,y),.0016,aa);
    }
    base+=azure*l*lim; base+=rose*line2(p,vec2(-.031,0.),vec2(.031,0.),.0033,aa);
    base+=digits(uv,vec2(.54,.792),vec2(.049,.071),180.+roll*110.,3)*.88;
  }else if(index==2){
    for(int i=0;i<2;i++){
      float y=(234.+265.*float(i))/720., a=i==0?pitch*3.5:roll*1.8;
      float wave=y+.077*sin(uv.x*7.4+phase*3.+float(i)*1.7)*(.45+a);
      if(uv.x>.068&&uv.x<.925)base+=azure*exp(-sq((uv.y-wave)/.0035))*.9;
      base+=digits(uv,vec2(.67,y-.18),vec2(.055,.070),abs(a*120.),2)*.78;
    }
  }else if(index==3){
    for(int i=0;i<2;i++){
      vec2 p=(uv-vec2((181.+280.*float(i))/640.,282./720.))*vec2(640./720.,1.);
      float angle=PI*(.74+1.52*(power+(i==0?-.38:.38)*roll));
      base+=azure*line2(p,vec2(0.),.106*vec2(cos(angle),sin(angle)),.003,aa);
      base+=rose*(1.-smoothstep(.007,.010,length(p)));
    }
    base+=digits(uv,vec2(.52,.67),vec2(.073,.098),power*100.,2);
  }else{
    for(int j=0;j<6;j++){
      float level=.5+.5*sin(phase*(2.+float(j))+float(j));
      float x=(279.+20.*(9.+floor(2.999*level)))/640.;
      vec2 p=(uv-vec2(x,(184.+64.*float(j))/720.))/vec2(.012,.010);
      base+=azure*(1.-smoothstep(.85,1.,max(abs(p.x),abs(p.y))))*(.17+.17*level);
    }
  }
  return clamp(base*vec3(.91,.96,1.07)+vec3(.018,.019,.04),0.,1.);
}
