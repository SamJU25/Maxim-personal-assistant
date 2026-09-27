import '@testing-library/jest-dom';

// Polyfill scrollIntoView for jsdom
if (!window.HTMLElement.prototype.scrollIntoView) {
  window.HTMLElement.prototype.scrollIntoView = () => {};
}

// Polyfill HTMLCanvasElement.prototype.getContext for jsdom
// jsdom has a stub that throws 'Not implemented', so override unconditionally
// @ts-expect-error Mocking canvas 2d context for jsdom
HTMLCanvasElement.prototype.getContext = () => ({
  clearRect: () => {},
  fillRect: () => {},
  beginPath: () => {},
  moveTo: () => {},
  lineTo: () => {},
  stroke: () => {},
  fill: () => {},
  arc: () => {},
  roundRect: () => {},
  createLinearGradient: () => ({
    addColorStop: () => {},
  }),
});
