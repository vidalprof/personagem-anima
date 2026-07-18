'use strict';
// ============================================================================
// MUNDO com SPRITES REAIS (kit LPC Base Assets, CC0) — nada desenhado por codigo.
//   chao de grama · arvores (sprite) com COLISAO · lago (sprite) · canteiro de
//   terra · personagem LPC animado (4 direcoes) · camera que SEGUE (explorar) ·
//   vento balancando as arvores · sons (vento + passaro + passos).
// Phaser CANVAS + Arcade (leve p/ PC antigo da escola).
// ============================================================================
const F = 64, HERO_SC = 1.0, WW = 1280, WH = 960, ZOOM = 1.6;
const IDLE = { up: 104, left: 117, down: 130, right: 143 };

// ---------- SOM (Web Audio proprio, comeca no 1o toque/tecla) --------------
let AC = null, MASTER = null, _windGain = null, _somOn = false;
function initSom() {
  if (AC) { if (AC.state === 'suspended') AC.resume(); return; }
  try {
    AC = new (window.AudioContext || window.webkitAudioContext)();
    MASTER = AC.createGain(); MASTER.gain.value = 0.6; MASTER.connect(AC.destination);
    const buf = AC.createBuffer(1, AC.sampleRate * 2, AC.sampleRate);
    const d = buf.getChannelData(0); let last = 0;
    for (let i = 0; i < d.length; i++) { const wn = Math.random() * 2 - 1; last = (last + 0.02 * wn) / 1.02; d[i] = last * 3.2; }
    const src = AC.createBufferSource(); src.buffer = buf; src.loop = true;
    const lp = AC.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 520;
    _windGain = AC.createGain(); _windGain.gain.value = 0.05;
    src.connect(lp); lp.connect(_windGain); _windGain.connect(MASTER); src.start();
    _somOn = true;
  } catch (e) { }
}
function rajadaSom() {
  if (!_windGain || !AC) return;
  const t = AC.currentTime;
  _windGain.gain.cancelScheduledValues(t); _windGain.gain.setValueAtTime(_windGain.gain.value, t);
  _windGain.gain.linearRampToValueAtTime(0.12, t + 0.8); _windGain.gain.linearRampToValueAtTime(0.05, t + 2.6);
}
function passarinho() {
  if (!AC || !_somOn) return;
  const t0 = AC.currentTime, n = 2 + (Math.random() < 0.5 ? 1 : 0);
  for (let k = 0; k < n; k++) {
    const t = t0 + k * 0.16, o = AC.createOscillator(), g = AC.createGain();
    o.type = 'sine'; o.frequency.setValueAtTime(2100 + Math.random() * 400, t);
    o.frequency.exponentialRampToValueAtTime(3000 + Math.random() * 500, t + 0.09);
    g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.09, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.13);
    o.connect(g); g.connect(MASTER); o.start(t); o.stop(t + 0.14);
  }
}
function passo() {
  if (!AC || !_somOn) return;
  const t = AC.currentTime, o = AC.createOscillator(), g = AC.createGain();
  o.type = 'triangle'; o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(70, t + 0.08);
  g.gain.setValueAtTime(0.05, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
  o.connect(g); g.connect(MASTER); o.start(t); o.stop(t + 0.13);
}

class Mundo extends Phaser.Scene {
  constructor() { super('Mundo'); }
  preload() {
    const B = 'assets/mundo/cut/';
    this.load.image('grass', B + 'grass1.png');
    this.load.image('grass2', B + 'grass0.png');
    this.load.image('dirt', B + 'dirt.png');
    this.load.image('tree', B + 'tree.png');
    this.load.image('pine', B + 'pine.png');
    this.load.image('pond', B + 'pond.png');
    this.load.spritesheet('hero', 'assets/hero.png', { frameWidth: F, frameHeight: F });
  }

  create() {
    // ---- CHAO: grama repetida (1 desenho, leve) ----
    this.add.tileSprite(0, 0, WW, WH, 'grass').setOrigin(0).setDepth(-100);

    // ---- CANTEIRO de terra (o "quadrado marrom": onde a crianca planta) ----
    this.add.tileSprite(560, 430, 160, 128, 'dirt').setOrigin(0).setDepth(-90);

    // colisores (arvores/lago) — corpos estaticos invisiveis, separados do visual
    this.blocos = this.physics.add.staticGroup();
    const solido = (x, y, w, h) => { const z = this.add.zone(x, y, w, h); this.physics.add.existing(z, true); this.blocos.add(z); };

    // ---- LAGO (sprite real) + colisao no espelho d'agua ----
    const lago = this.add.image(240, 720, 'pond').setDepth(720);
    solido(lago.x, lago.y + 6, 78, 54);

    // ---- ARVORES (sprite real): redondas + pinheiros, com COLISAO no tronco ----
    const arvores = [
      ['tree', 140, 180], ['tree', 420, 150], ['pine', 700, 130], ['tree', 980, 200],
      ['pine', 1120, 320], ['tree', 1080, 560], ['tree', 300, 430], ['pine', 120, 560],
      ['tree', 500, 780], ['pine', 820, 820], ['tree', 1160, 800], ['tree', 940, 380],
      ['pine', 1000, 650], ['tree', 380, 900],
    ];
    arvores.forEach(([tipo, x, y], i) => {
      const a = this.add.image(x, y, tipo).setOrigin(0.5, 1).setDepth(y);
      this.tweens.add({ targets: a, angle: { from: -1.6, to: 1.6 }, duration: 2000 + (i % 5) * 220, yoyo: true, repeat: -1, ease: 'Sine.inOut', delay: (i % 7) * 250 });
      const larg = tipo === 'pine' ? 16 : 22;
      solido(x, y - 7, larg, 14);   // colisao so na base do tronco
    });

    // ---- ANIMACOES do heroi (LPC: 8 quadros por direcao) ----
    this.anims.create({ key: 'up', frames: this.anims.generateFrameNumbers('hero', { start: 105, end: 112 }), frameRate: 9, repeat: -1 });
    this.anims.create({ key: 'left', frames: this.anims.generateFrameNumbers('hero', { start: 118, end: 125 }), frameRate: 9, repeat: -1 });
    this.anims.create({ key: 'down', frames: this.anims.generateFrameNumbers('hero', { start: 131, end: 138 }), frameRate: 9, repeat: -1 });
    this.anims.create({ key: 'right', frames: this.anims.generateFrameNumbers('hero', { start: 144, end: 151 }), frameRate: 9, repeat: -1 });

    // ---- SOMBRA do heroi (elipse suave — grounding, discreta) ----
    this.sombra = this.add.ellipse(WW / 2, WH / 2, 34, 13, 0x000000, 0.22);

    // ---- HEROI ----
    this.hero = this.physics.add.sprite(WW / 2, WH / 2, 'hero', IDLE.down).setScale(HERO_SC);
    this.hero.body.setSize(20, 16).setOffset(22, 44);   // corpo pequeno nos pes
    this.hero.setCollideWorldBounds(true);
    this.physics.add.collider(this.hero, this.blocos);
    this.dir = 'down'; this._passoT = 0; this._forc = null;
    this.cursors = this.input.keyboard.createCursorKeys();
    this.wasd = this.input.keyboard.addKeys('W,A,S,D');

    // ---- CAMERA que segue (clima de explorar) ----
    this.physics.world.setBounds(0, 0, WW, WH);
    this.cameras.main.setBounds(0, 0, WW, WH);
    this.cameras.main.setZoom(ZOOM);
    this.cameras.main.startFollow(this.hero, true, 0.12, 0.12);

    // ---- vento (som) + passarinho de tempos em tempos ----
    this.time.addEvent({ delay: 5000, loop: true, callback: rajadaSom });
    this.time.addEvent({ delay: 4200, loop: true, callback: () => { if (Math.random() < 0.7) passarinho(); } });

    // ---- liga o som no 1o gesto ----
    const liga = () => { initSom(); const dica = document.getElementById('somdica'); if (dica) dica.style.display = 'none'; };
    this.input.on('pointerdown', liga);
    this.input.keyboard.on('keydown', liga);

    window.__ready = true;
    window.__scene = this;
    window.__mover = (dir) => { this._forc = dir; };
    window.__parar = () => { this._forc = null; };
    window.__fs = () => { if (this.scale.isFullscreen) this.scale.stopFullscreen(); else this.scale.startFullscreen(); };
  }

  update(time) {
    let vx = 0, vy = 0;
    if (this.cursors.left.isDown || this.wasd.A.isDown || this._forc === 'left') vx = -1;
    else if (this.cursors.right.isDown || this.wasd.D.isDown || this._forc === 'right') vx = 1;
    else if (this.cursors.up.isDown || this.wasd.W.isDown || this._forc === 'up') vy = -1;
    else if (this.cursors.down.isDown || this.wasd.S.isDown || this._forc === 'down') vy = 1;

    this.hero.body.setVelocity(vx * 150, vy * 150);
    const andando = vx !== 0 || vy !== 0;
    if (vx < 0) { this.hero.anims.play('left', true); this.dir = 'left'; }
    else if (vx > 0) { this.hero.anims.play('right', true); this.dir = 'right'; }
    else if (vy < 0) { this.hero.anims.play('up', true); this.dir = 'up'; }
    else if (vy > 0) { this.hero.anims.play('down', true); this.dir = 'down'; }
    else { this.hero.anims.stop(); this.hero.setFrame(IDLE[this.dir]); }

    this.hero.setDepth(this.hero.y);           // y-sort: passa atras/frente das arvores
    this.sombra.setPosition(this.hero.x, this.hero.y + 26).setDepth(this.hero.y - 1);
    this.sombra.scaleY = andando ? 0.9 : 1;

    if (andando && time - this._passoT > 300) { passo(); this._passoT = time; }
  }
}

new Phaser.Game({
  type: Phaser.CANVAS, pixelArt: true, roundPixels: true, backgroundColor: '#3f6a34',
  physics: { default: 'arcade', arcade: {} },
  // RESIZE = preenche a janela inteira; pixelArt mantem NITIDO (nearest-neighbor).
  scale: { mode: Phaser.Scale.RESIZE, parent: 'jogo', width: '100%', height: '100%' },
  scene: Mundo
});
