#!/usr/bin/env node
// render_video.js — puppeteer frame-by-frame capture -> ffmpeg pipe
// Usage: node --max-old-space-size=4096 render_video.js

const puppeteer = require('puppeteer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const HTML_PATH = path.resolve(__dirname, 'cinematic_intro_video.html');
const OUT_PATH = path.resolve(__dirname, 'cinematic_intro.mp4');
const FPS = 30;
const TOTAL_FRAMES = 270; // 9s
const WIDTH = 1920;
const HEIGHT = 1080;

async function main() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-web-security',
      '--allow-file-access-from-files',
      '--autoplay-policy=no-user-gesture-required',
      '--disable-features=IsolateOrigins,site-per-process',
      `--window-size=${WIDTH},${HEIGHT}`,
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT });

  console.log('Loading HTML...');
  await page.goto(`file://${HTML_PATH}`, { waitUntil: 'domcontentloaded', timeout: 30000 });

  // Wait for animationReady
  await page.waitForFunction('window.animationReady === true', { timeout: 10000 });

  // Stagger videos and wait for them to start
  await page.evaluate(() => {
    document.querySelectorAll('video').forEach(v => {
      v.currentTime = Math.random() * 3;
      v.play().catch(() => {});
    });
  });

  // Small delay to let videos actually start decoding
  await new Promise(r => setTimeout(r, 2000));

  console.log('Starting ffmpeg pipe...');
  const ffmpeg = spawn('ffmpeg', [
    '-y',
    '-f', 'image2pipe',
    '-r', String(FPS),
    '-i', 'pipe:0',
    '-vf', `scale=${WIDTH}:${HEIGHT}`,
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-crf', '20',
    '-pix_fmt', 'yuv420p',
    OUT_PATH,
  ]);

  ffmpeg.stderr.on('data', d => process.stderr.write(d));
  ffmpeg.stdout.on('data', d => process.stdout.write(d));

  let ffmpegDone = false;
  const ffmpegPromise = new Promise((resolve, reject) => {
    ffmpeg.on('close', code => {
      ffmpegDone = true;
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited with code ${code}`));
    });
  });

  console.log(`Capturing ${TOTAL_FRAMES} frames at ${FPS}fps...`);
  for (let frame = 0; frame < TOTAL_FRAMES; frame++) {
    await page.evaluate(f => window.setFrame(f), frame);

    // Give videos a tick to render
    await new Promise(r => setTimeout(r, 0));

    const png = await page.screenshot({
      type: 'png',
      clip: { x: 0, y: 0, width: WIDTH, height: HEIGHT },
    });

    await new Promise((resolve, reject) => {
      ffmpeg.stdin.write(png, err => {
        if (err) reject(err);
        else resolve();
      });
    });

    if (frame % 30 === 0) {
      console.log(`  Frame ${frame}/${TOTAL_FRAMES} (${Math.round(frame/TOTAL_FRAMES*100)}%)`);
    }
  }

  console.log('Closing stdin...');
  ffmpeg.stdin.end();
  await ffmpegPromise;

  await browser.close();
  console.log(`Done! Output: ${OUT_PATH}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
