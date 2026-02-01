let intervalVibrate: number;
export function vibrate(pattern: number[] = [25], keep = false) {
  // console.debug("vibrate", pattern, keep);
  clearInterval(intervalVibrate);
  try {
    navigator.vibrate(0);
  } catch (e) {
    console.warn((e as Error).message);
    return;
  }
  if (keep && Array.isArray(pattern)) {
    if (pattern[0]! < 0 || pattern[0]! > 1e25) {
      pattern = [1e25];
    } else {
      intervalVibrate = window.setInterval(
        () => {
          navigator.vibrate(pattern);
        },
        pattern.reduce((prev, now) => prev + now, 0),
      );
      return;
    }
  }
  navigator.vibrate(pattern);
}

/** @returns removeEventListener */
export function globalVibrate(element: (typeof HTMLElement)[] = [HTMLButtonElement]) {
  function vibrateIf(event: PointerEvent) {
    for (const cls of element) {
      if (event.target instanceof cls) {
        vibrate();
        return;
      }
    }
  }
  // 使用事件委托，在document级别捕获所有按钮点击
  document.addEventListener("click", vibrateIf);
  return () => {
    document.removeEventListener("click", vibrateIf);
  };
}
