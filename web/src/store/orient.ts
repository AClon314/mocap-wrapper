import { ref, reactive, computed, watch } from "vue";
import { defineStore } from "pinia";

export const __name__ = "orient";
export let _isMounted = false;
/**
 * @example Usage:
 * ```ts
import { useOrientStore } from './stores/orient';
const orient = useOrientStore();
watchEffect(() => {
  document.body.style.setProperty('--angle', orient.smooth.theta.toFixed(2));
});
 * ```
 */
export const useOrientStore = defineStore(__name__, () => {
  /** -1~1 */
  const cursor = reactive({
    /** - */
    x: 0,
    /** | */
    y: 0,
  });
  const orient = reactive({
    /** -180~180, beta, front/back */
    x: 0,
    /** -180~180, gamma, left/right */
    y: 0,
    /** 0~360, alpha, z-compass */
    z: 0,
  });
  /** 0~1, raw cursor/orientation */
  const pos = computed(() => ({
    x: cursor.x + orient.x / -180,
    y: cursor.y + orient.y / -180,
    z: orient.z / 360,
  }));
  /** EMA smooth of rawPos */
  const smooth = reactive({
    r: 0,
    theta: 0,
    x: 0,
    y: 0,
    z: 0,
    /** 0~1, smaller for smoother */
    factor: 0.1,
  });
  function calcSmooth() {
    smooth.x += (pos.value.x - smooth.x) * smooth.factor;
    smooth.y += (pos.value.y - smooth.y) * smooth.factor;
    smooth.z += (pos.value.z - smooth.z) * smooth.factor;
    // radient, center (0.5, 0.5)
    const { x, y } = smooth;
    smooth.r = Math.sqrt(x * x + y * y) * Math.SQRT2;
    smooth.theta = Math.atan2(y, x);
  }
  watch(
    pos,
    () => {
      calcSmooth();
    },
    { immediate: true },
  );

  function onMouseMove(event: MouseEvent) {
    const { clientX, clientY } = event;
    const { innerWidth, innerHeight } = window;
    // normalized 0~1
    cursor.x = (clientX / innerWidth) * 2 - 1;
    cursor.y = (clientY / innerHeight) * 2 - 1;
    return cursor;
  }
  function onOrient(event: DeviceOrientationEvent) {
    const { alpha, beta, gamma } = event;
    if (gamma != null) orient.x = gamma;
    if (beta != null) orient.y = beta;
    if (alpha != null) orient.z = alpha;
    return orient;
  }
  const granted = ref(false);
  async function canOrient() {
    if (!window.isSecureContext) {
      console.warn("DeviceOrientationEvent need HTTPS.");
      return false;
    }
    // const permissions = await Promise.all([
    //   navigator.permissions.query({ name: "gyroscope" }),
    //   navigator.permissions.query({ name: "accelerometer" }),
    // ])
    // const bool = permissions.every(perm => perm.state === "granted");
    if (!window.DeviceOrientationEvent) {
      console.warn("DeviceOrientationEvent is NOT supported by this browser.");
    }
    return !!window.DeviceOrientationEvent;
  }

  async function mount() {
    console.debug("orient store mount", _isMounted);
    if (_isMounted) return;
    _isMounted = true;
    window.addEventListener("mousemove", onMouseMove);
    granted.value = await canOrient();
    if (granted.value) {
      window.addEventListener("deviceorientation", onOrient);
    }
  }
  function unmount() {
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("deviceorientation", onOrient);
  }

  if (!_isMounted) mount(); // auto mount
  return { orient, cursor, pos, smooth, granted, canOrient, mount, unmount };
});
