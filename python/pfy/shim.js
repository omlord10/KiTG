// --- минимальные шимы браузерных API для офлайн-запуска движка в Node ---
function makeCtx() {
  return {
    font: '', fillStyle: '', strokeStyle: '', lineWidth: 1, textAlign: '', textBaseline: '',
    measureText: (t) => ({ width: (t ? t.length : 0) * 8 }),
    beginPath(){}, closePath(){}, moveTo(){}, lineTo(){}, arc(){}, arcTo(){}, fill(){},
    stroke(){}, fillRect(){}, clearRect(){}, fillText(){}, strokeText(){}, save(){}, restore(){},
    translate(){}, rotate(){}, scale(){}, setTransform(){}, setLineDash(){}, quadraticCurveTo(){},
    bezierCurveTo(){}, rect(){}, clip(){}, drawImage(){}, createLinearGradient(){return {addColorStop(){}}},
  };
}
function makeEl(tag) {
  const el = {
    tagName: tag, style: {}, width: 1200, height: 800, className: '', id: '',
    children: [], offsetHeight: 0, offsetWidth: 0,
    getContext: () => makeCtx(),
    addEventListener(){}, removeEventListener(){}, appendChild(c){this.children.push(c); return c;},
    setAttribute(){}, getAttribute(){return null;}, focus(){}, blur(){}, click(){},
    getBoundingClientRect(){return {left:0,top:0,width:0,height:0};},
    toDataURL(){return 'data:image/png;base64,';},
    classList: { add(){}, remove(){}, toggle(){}, contains(){return false;} },
    querySelector(){return makeEl('div');}, querySelectorAll(){return [];},
  };
  return el;
}
const documentShim = {
  getElementById: () => makeEl('div'),
  getElementsByClassName: () => [makeEl('div')],
  getElementsByTagName: () => [makeEl('div')],
  querySelector: () => makeEl('div'),
  querySelectorAll: () => [],
  createElement: (t) => makeEl(t),
  createElementNS: (ns, t) => makeEl(t),
  addEventListener(){}, removeEventListener(){},
  body: makeEl('body'), head: makeEl('head'), documentElement: makeEl('html'),
  cookie: '',
};
global.document = documentShim;
global.window = global;
global.navigator = { userAgent: 'node', platform: 'node', language: 'ru' };
global.location = { href: 'file:///', protocol: 'file:', host: '' };
global.innerWidth = 1200; global.innerHeight = 800;
global.devicePixelRatio = 1;
global.requestAnimationFrame = () => 0;
global.cancelAnimationFrame = () => {};
global.setTimeout = global.setTimeout || (() => 0);
global.localStorage = { getItem: () => null, setItem(){}, removeItem(){}, clear(){} };
global.Image = function(){ return makeEl('img'); };
global.alert = () => {}; global.confirm = () => true; global.prompt = () => '';
global.addEventListener = () => {}; global.removeEventListener = () => {};
global.matchMedia = () => ({ matches:false, addListener(){}, removeListener(){} });
// jQuery shim: $(document).ready(fn) НЕ вызывает fn (чтобы не стартовал bootstrap)
const $shim = function() {
  return { ready(){}, on(){return this;}, off(){return this;}, click(){return this;},
           val(){return '';}, html(){return this;}, text(){return this;}, css(){return this;},
           attr(){return this;}, addClass(){return this;}, removeClass(){return this;},
           append(){return this;}, find(){return $shim();}, each(){return this;},
           width(){return 0;}, height(){return 0;}, hide(){return this;}, show(){return this;} };
};
$shim.ajax = () => {}; $shim.get = () => {}; $shim.post = () => {};
global.$ = $shim; global.jQuery = $shim;
// аналитика
global.Ya = function(){}; global.ym = () => {}; global.gtag = () => {}; global.dataLayer = [];
