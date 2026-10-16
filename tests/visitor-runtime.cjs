'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'visitor-stats', 'visitor-stats.js'), 'utf8');
const totalUrl = 'https://s01.flagcounter.com/mini/FeUW/bg_FFFFFF/txt_285E91/border_FFFFFF/flags_0/';
const widgetUrls = [totalUrl];

function makeRuntime({ hostname = 'localhost', pathname = '/index.html', search = '' } = {}) {
  const requests = [];
  const timers = new Map();
  let nextTimerId = 0;
  const statuses = widgetUrls.map(() => ({ textContent: 'Loading total page views…', hidden: false }));
  const images = widgetUrls.map((url, index) => {
    const listeners = new Map();
    let src;
    return {
      dataset: { visitorSrc: url },
      hidden: true,
      get src() { return src; },
      set src(value) { src = value; requests.push(value); },
      closest(selector) {
        assert.equal(selector, 'figure');
        return {
          querySelector(statusSelector) {
            assert.equal(statusSelector, '.hydra-visitors-status');
            return statuses[index];
          },
        };
      },
      addEventListener(type, callback, options = {}) {
        const entries = listeners.get(type) || [];
        entries.push({ callback, once: options.once });
        listeners.set(type, entries);
      },
      dispatch(type) {
        for (const entry of [...(listeners.get(type) || [])]) {
          if (entry.once) {
            listeners.set(type, listeners.get(type).filter(candidate => candidate !== entry));
          }
          entry.callback();
        }
      },
    };
  });
  const panel = {
    dataset: { visitorHost: 'bollossom.github.io', visitorPath: '/HYDRA/' },
    querySelectorAll(selector) {
      assert.equal(selector, '[data-visitor-src]');
      return images;
    },
  };
  const context = vm.createContext({
    URLSearchParams,
    document: {
      querySelectorAll(selector) {
        assert.equal(selector, '[data-visitor-host]');
        return [panel];
      },
    },
    window: {
      location: { hostname, pathname, search },
      setTimeout(callback, delay) {
        const id = ++nextTimerId;
        timers.set(id, { callback, delay });
        return id;
      },
      clearTimeout(id) { timers.delete(id); },
      setInterval() { assert.fail('Visitor widgets must not automatically refresh.'); },
    },
  });
  return {
    requests, timers, statuses, images,
    run() { vm.runInContext(source, context, { filename: 'visitor-stats.js' }); },
    fireTimers() {
      for (const [id, timer] of [...timers]) {
        timers.delete(id);
        timer.callback();
      }
    },
  };
}

function makeLiveRuntime() {
  return makeRuntime({ hostname: 'bollossom.github.io', pathname: '/HYDRA/index.html' });
}

test('local and offline previews do not request tracking images', () => {
  for (const location of [
    { hostname: 'localhost', pathname: '/HYDRA/index.html' },
    { hostname: '127.0.0.1', pathname: '/HYDRA/' },
    { hostname: '', pathname: '/archive/HYDRA/index.html' },
  ]) {
    const runtime = makeRuntime(location);
    runtime.run();
    assert.deepEqual(runtime.requests, []);
    assert.equal(runtime.timers.size, 0);
    runtime.images.forEach(image => assert.equal(image.src, undefined));
    runtime.statuses.forEach(status => {
      assert.match(status.textContent, /Open the live website/);
      assert.equal(status.hidden, false);
    });
  }
});

test('the exact production host and project path start one total-page-views widget immediately', () => {
  for (const pathname of ['/HYDRA/', '/HYDRA/index.html', '/HYDRA/training-logs/']) {
    const runtime = makeRuntime({ hostname: 'bollossom.github.io', pathname });
    runtime.run();
    assert.deepEqual(runtime.requests, widgetUrls);
    assert.equal(runtime.timers.size, 1);
    runtime.images.forEach(image => assert.equal(image.hidden, true));
  }
});

test('unrelated paths and lookalike hosts cannot count production visits', () => {
  for (const location of [
    { hostname: 'bollossom.github.io', pathname: '/' },
    { hostname: 'bollossom.github.io', pathname: '/OTHER/index.html' },
    { hostname: 'bollossom.github.io', pathname: '/HYDRA-other/' },
    { hostname: 'bollossom.github.io', pathname: '/hydra/' },
    { hostname: 'bollossom.github.io.example.com', pathname: '/HYDRA/' },
  ]) {
    const runtime = makeRuntime(location);
    runtime.run();
    assert.deepEqual(runtime.requests, []);
    assert.equal(runtime.timers.size, 0);
  }
});

test('the explicit preview query enables local inspection', () => {
  const enabled = makeRuntime({ search: '?other=value&visitor-preview=1' });
  enabled.run();
  assert.deepEqual(enabled.requests, widgetUrls);
  for (const search of ['?visitor-preview=0', '?visitor-preview=true', '?visitor-preview=']) {
    const disabled = makeRuntime({ search });
    disabled.run();
    assert.deepEqual(disabled.requests, []);
  }
});

test('successful widget loads reveal their images and clear loading timeouts', () => {
  const runtime = makeLiveRuntime();
  runtime.run();
  runtime.images.forEach((image, index) => {
    image.dispatch('load');
    assert.equal(image.hidden, false);
    assert.equal(runtime.statuses[index].hidden, true);
  });
  assert.equal(runtime.timers.size, 0);
  runtime.fireTimers();
  assert.deepEqual(runtime.requests, widgetUrls);
});

test('failed widget loads display a report fallback and clear loading timeouts', () => {
  const runtime = makeLiveRuntime();
  runtime.run();
  runtime.images.forEach((image, index) => {
    image.dispatch('error');
    assert.equal(image.hidden, true);
    assert.equal(runtime.statuses[index].hidden, false);
    assert.match(runtime.statuses[index].textContent, /temporarily unavailable.*full report/);
  });
  assert.equal(runtime.timers.size, 0);
  runtime.fireTimers();
  runtime.statuses.forEach(status => assert.match(status.textContent, /temporarily unavailable/));
});

test('slow loads show a useful status and can still complete or fail', () => {
  for (const result of ['load', 'error']) {
    const runtime = makeLiveRuntime();
    runtime.run();
    for (const timer of runtime.timers.values()) assert.equal(timer.delay, 15000);
    runtime.fireTimers();
    assert.match(runtime.statuses[0].textContent, /longer to load.*full report/);
    runtime.images[0].dispatch(result);
    assert.equal(runtime.images[0].hidden, result === 'error');
    assert.equal(runtime.statuses[0].hidden, result === 'load');
    if (result === 'error') assert.match(runtime.statuses[0].textContent, /temporarily unavailable/);
    assert.equal(runtime.timers.size, 0);
  }
});

test('reinvoking the script does not request widgets or schedule timers twice', () => {
  const runtime = makeLiveRuntime();
  runtime.run();
  runtime.run();
  assert.deepEqual(runtime.requests, widgetUrls);
  assert.equal(runtime.timers.size, 1);
  runtime.images.forEach(image => image.dispatch('load'));
  runtime.run();
  assert.deepEqual(runtime.requests, widgetUrls);
  assert.equal(runtime.timers.size, 0);
});

test('elapsed time never causes an automatic refresh or additional counted requests', () => {
  const runtime = makeLiveRuntime();
  runtime.run();
  runtime.fireTimers();
  runtime.fireTimers();
  runtime.fireTimers();
  assert.deepEqual(runtime.requests, widgetUrls);
  assert.equal(runtime.timers.size, 0);
});