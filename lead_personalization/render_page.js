#!/usr/bin/env node
/**
 * Headless-render a lead website and print page signals as JSON.
 * Fallback for JS-rendered sites (Wix, Squarespace, React) where a plain
 * HTTP fetch returns no usable title/meta/h1.
 *
 * Usage: node render_page.js <url> [timeout_ms]
 * Output (stdout): {"title","description","h1","has_video","fetched","error"}
 */

const { chromium } = require('playwright');

const VIDEO_EVIDENCE =
  /youtube\.com\/embed|youtube-nocookie\.com|player\.vimeo\.com|fast\.wistia|<video\b|\.mp4\b|loom\.com\/embed/i;

const out = {
  title: '',
  description: '',
  h1: '',
  has_video: false,
  fetched: false,
  error: '',
};

function exitWithJson(data) {
  try {
    process.stdout.write(JSON.stringify(data));
  } catch (_) {
    process.stdout.write('{"title":"","description":"","h1":"","has_video":false,"fetched":false,"error":"serialization failure"}');
  }
}

process.on('uncaughtException', (err) => {
  out.error = String((err && err.message) || err).slice(0, 120);
  exitWithJson(out);
  process.exit(0);
});

process.on('unhandledRejection', (reason) => {
  out.error = String((reason && (reason.message || reason)) || 'unhandled rejection').slice(0, 120);
  exitWithJson(out);
  process.exit(0);
});

(async () => {
  const rawUrl = (process.argv[2] || '').trim();
  const parsedTimeout = parseInt(process.argv[3] || '20000', 10);
  const timeout = Math.max(1000, Math.min(isNaN(parsedTimeout) ? 20000 : parsedTimeout, 60000));

  if (!rawUrl || !/^https?:\/\//i.test(rawUrl)) {
    out.error = 'invalid url';
    exitWithJson(out);
    return;
  }
  const url = rawUrl;

  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({
      userAgent: 'Mozilla/5.0 (compatible; AevoraLeadResearch/1.0)',
      viewport: { width: 1280, height: 800 },
    });
    await page.goto(url, { timeout, waitUntil: 'domcontentloaded' });
    // Give client-side frameworks a moment to paint real content.
    await page.waitForTimeout(2000);

    out.fetched = true;
    out.title = (await page.title()) || '';

    const dom = await page.evaluate(() => {
      const meta = document.querySelector('meta[name="description" i]');
      const h1 = document.querySelector('h1');
      return {
        description: meta ? meta.getAttribute('content') || '' : '',
        h1: h1 ? (h1.textContent || '').trim() : '',
        hasVideoEl: Boolean(
          document.querySelector('video, iframe[src*="youtube"], iframe[src*="vimeo"], iframe[src*="wistia"], iframe[src*="loom"]')
        ),
      };
    });
    out.description = dom.description;
    out.h1 = dom.h1;

    const html = await page.content();
    out.has_video = dom.hasVideoEl || VIDEO_EVIDENCE.test(html);
  } catch (err) {
    out.error = String((err && err.message) || err).slice(0, 120);
  } finally {
    if (browser) await browser.close().catch(() => {});
  }

  exitWithJson(out);
})();
