#version 330 core
// SPDX-License-Identifier: GPL-3.0-only
out vec4 outputColor;
uniform vec2 resolution;
uniform float phase;
uniform sampler2D vistaTex, seatTex, shipTex, panelTex, reticleTex, originalTex;
const float PI=3.14159265359;
const float ASPECT=16.0/9.0;
const vec3 azure=vec3(.32,.52,.78), lavender=vec3(.57,.55,.79), rose=vec3(.72,.37,.49);
float sq(float x){return x*x;}
mat2 rot(float a){float c=cos(a),s=sin(a);return mat2(c,s,-s,c);}
vec2 spin(vec2 p,float angle){return (rot(angle)*(p*vec2(ASPECT,1.)))/vec2(ASPECT,1.);}
float line2(vec2 p,vec2 a,vec2 b,float w,float aa){
  vec2 d=b-a;float h=clamp(dot(p-a,d)/max(dot(d,d),.000001),0.,1.);
  return 1.-smoothstep(w-aa,w+aa,length(p-a-d*h));
}
vec3 over(vec3 under,vec3 lit,float a){return 1.-(1.-under)*(1.-lit*clamp(a,0.,1.));}
vec3 bankSample(float n,vec2 st){
  vec2 cell=vec2(mod(n,8.),floor(n/8.));
  return texture(originalTex,(cell+clamp(st,vec2(.002),vec2(.998)))/8.).rgb;
}
vec2 faceUV(vec2 p,vec2 a,vec2 b,vec2 c,vec2 d){
  float x=(p.x-a.x)/(b.x-a.x), y=0.;
  for(int i=0;i<2;i++){
    vec2 top=mix(a,b,x),bot=mix(d,c,x);y=(p.y-top.y)/(bot.y-top.y);
    vec2 le=mix(a,d,y),ri=mix(b,c,y);x=(p.x-le.x)/(ri.x-le.x);
  }
  return vec2(x,y);
}
#include "avionics.frag"
float exhaust(vec2 p,vec2 engine,float power,float seed){
  vec2 e=p-engine;float extent=.115+.055*power;
  if(e.x<-.012||e.x>extent*4.)return 0.;
  float v=max(e.x,0.)/extent;
  float axis=e.y + .11*e.x + .0009*sin(70.*e.x+phase*17.+seed)*min(v,1.);
  float width=.0065+.0065*v;
  float edge=smoothstep(-.011,.006,e.x);
  return edge*exp(-sq(axis/width))*exp(-2.25*v);
}
void main(){
  vec2 q=vec2(gl_FragCoord.x/resolution.x,1.-gl_FragCoord.y/resolution.y);
  float t=phase;
  float roll=.080*sin(2.*t-.56)+.043*sin(t+.20)+.015*sin(3.*t+.88);
  float pitch=.037*sin(2.*t+.42)+.013*sin(3.*t-.85);
  float yaw=.055*sin(t-.31)+.028*sin(2.*t+.91);
  float power=.53+.153*sin(2.*t-.74)+.071*sin(3.*t+.9);
  float driveR=.62*sin(2.*t-.37)+.30*sin(t+.39);
  float driveL=.64*sin(2.*t-.53)+.30*sin(3.*t+1.11);
  float breath=.00115*sin(37.*t)+.00040*sin(23.*t+.6);
  float glance=.5+.5*cos(t+1.36);
  vec2 head=vec2(.009*sin(t+.16)+.0035*sin(3.*t),.0052*sin(2.*t-.13)+breath);
  vec2 look=q+head*.43+vec2(.00,-.022*pow(glance,4.));
  vec2 skyPoint=spin(look-vec2(.5,.325),roll);
  vec2 bg=vec2(.5,.584)+skyPoint*vec2(.655,.81)+vec2(yaw+ .016*sin(t+.6),pitch);
  vec3 sky=texture(vistaTex,clamp(bg,.001,.999)).rgb;
  float dark=1.-smoothstep(.025,.32,max(max(sky.r,sky.g),sky.b));
  sky=clamp(sky*vec3(.88,.91,1.00)+vec3(.011,.014,.032)+dark*vec3(.016,.022,.055),0.,1.);
  // Each plane has its own parallax and inertia. The carrier stays in formation throughout the orbit.
  vec2 formation=vec2(.52+.204*cos(t+.54)+.038*sin(2.*t-.3),.222+.042*sin(t+.70));
  float size=.354+.103*cos(t-1.06)+.027*sin(2.*t);
  vec2 st=spin(look-vec2(.5,.325),roll)*vec2(1.)+vec2(.5,.325);
  st=(st-formation+vec2(yaw*.72,pitch*.63))/size;
  st=spin(st,-.018*sin(t+.9))+vec2(.5);
  if(st.y>-.02&&st.y<1.02&&st.x>-.02&&st.x<1.62){
    float plume=exhaust(st,vec2(.844,.687),power,.2)+exhaust(st,vec2(.887,.646),power,.8)
              +exhaust(st,vec2(.902,.584),power,.4)+exhaust(st,vec2(.932,.564),power,.9);
    sky=over(sky,vec3(.39,.65,1.),min(1.,plume*(.61+power*.50)));
    if(all(greaterThanEqual(st,vec2(0.)))&&all(lessThanEqual(st,vec2(1.)))){
      vec4 ship=texture(shipTex,st);
      vec3 hull=ship.rgb*vec3(.84,.88,.96)+ship.a*vec3(.012,.018,.04);
      sky=hull+sky*(1.-ship.a);
    }
  }
  vec2 pane=spin(q-vec2(.5,.39),roll*.12)+vec2(.5,.39)+head*.59+vec2(yaw*.06,-.012*pow(glance,4.));
  if(pane.y>0.&&pane.y<.47&&pane.x>0.&&pane.x<1.){
    vec4 h=texture(reticleTex,pane);
    sky=sky*(1.-h.a*.23)+h.rgb*(.75+.09*power);
    float originalFrame=(.5-.5*cos(t+.45))*63.;
    vec2 oldUV=vec2(pane.x,pane.y/.58);
    float sourceOutline=mix(bankSample(floor(originalFrame),oldUV).r,bankSample(min(63.,ceil(originalFrame)),oldUV).r,fract(originalFrame));
    sky=over(sky,vec3(.44,.17,.30),sourceOutline*.21*smoothstep(.18,.46,abs(pane.x-.5)));
    vec2 hp=pane*vec2(ASPECT,1.);
    float yy=.144+pitch*.68;
    float needle=line2(hp,vec2(.650*ASPECT,yy),vec2(.663*ASPECT,yy),.00065,.00040);
    sky=over(sky,rose,needle*.9);
    float aimX=.504+yaw*.27,aimY=.214+pitch*.32;
    vec2 marker=(pane-vec2(aimX,aimY))*vec2(ASPECT,1.);
    float ring=1.-smoothstep(.00031,.00095,abs(length(marker)-.0044));
    sky=over(sky,azure,ring*.48);
  }
  // The right-hand grip starts the bank slightly before the horizon follows; the left tracks thrust.
  vec2 cp=spin(q-vec2(.5,.71),roll*.047)+vec2(.5,.71)-head;
  cp.x=(cp.x-.5)/1.035+.5;
  cp.y=(cp.y-(.131-.040*pow(glance,4.)))/.897;
  if(cp.y>=.35){
    float handZone=smoothstep(.695,.741,cp.y)*(1.-smoothstep(.9,1.06,cp.y));
    float left=exp(-sq((cp.x-.193)/.091)-sq((cp.y-.79)/.17))*handZone;
    float right=exp(-sq((cp.x-.805)/.094)-sq((cp.y-.79)/.17))*handZone;
    cp-=left*vec2(.0085*driveL,.0125*driveL)+right*vec2(.0128*driveR,-.0075*driveR);
    vec4 fg=texture(seatTex,clamp(cp,.0001,.9999));
    vec3 lit=fg.rgb*vec3(.84+.027*power,.85+.022*power,.943)+fg.a*vec3(.004,.009,.018);
    if(cp.y<.687&&cp.y>.385&&cp.x>.095&&cp.x<.905){
      vec2 pos=cp*vec2(1672.,941.),uv;int index;
      if(pos.x<344.){index=1;uv=faceUV(pos,vec2(191,410),vec2(335,432),vec2(320,615),vec2(175,589));}
      else if(pos.x<536.){index=2;uv=faceUV(pos,vec2(362,434),vec2(523,434),vec2(518,635),vec2(353,635));}
      else if(pos.x<1135.){index=0;uv=faceUV(pos,vec2(562,375),vec2(1110,375),vec2(1120,609),vec2(552,609));}
      else if(pos.x<1331.){index=3;uv=faceUV(pos,vec2(1149,434),vec2(1309,434),vec2(1321,635),vec2(1152,635));}
      else {index=4;uv=faceUV(pos,vec2(1336,432),vec2(1480,410),vec2(1495,589),vec2(1344,616));}
      if(all(greaterThan(uv,vec2(.001)))&&all(lessThan(uv,vec2(.999)))){
        float edge=min(min(uv.x,1.-uv.x),min(uv.y,1.-uv.y));
        float glass=(1.-smoothstep(.115,.245,fg.r))*fg.a*smoothstep(.0005,.007,edge);
        vec3 emission=instrument(index,uv,roll,pitch,power,driveR,driveL);
        lit=mix(lit,emission,glass);
      }
    }
    sky=lit+sky*(1.-fg.a);
  }
  outputColor=vec4(clamp(sky,0.,1.),1.);
}
