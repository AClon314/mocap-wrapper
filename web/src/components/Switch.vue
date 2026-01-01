<!-- https://uiverse.io/Nawsome/empty-snail-69 -->
<template>
  <input type="checkbox" class="switch" :="$attrs" />
</template>

<style scoped>
.switch {
  --motion-duration: 2s;
  appearance: none;
  display: block;
  width: 200px;
  height: 100px;
  background-color: #9b0621;
  position: relative;
  cursor: pointer;
  border-radius: 5px;
  
  /* 3D Transform Setup */
  transform: perspective(700px) translateZ(20px) rotateY(-25deg);
  transform-style: preserve-3d;
  transition: all var(--motion-duration, 0.3s) cubic-bezier(1, 0, 1, 1);
  transform-origin: center center -20px;

  /* Composite Background Layering:
     1. Shadow (Depth)
     2. Gloss/Shine (Top & Gloss)
     3. Characters (I and O)
     4. Dots Pattern
     5. Light (Glow) - Hidden by default
     6. Base Gradient
  */
  background-image:
    /* 1. Shadow: favors right side initially (unchecked) */
    linear-gradient(to right, transparent 70%, rgba(0, 0, 0, 0.8)),
    
    /* 2. Shine: Top edge highlight & Surface gloss */
    linear-gradient(to bottom, white, transparent 3%),
    linear-gradient(to right, rgba(255, 255, 255, 0.5), transparent 50%, transparent 80%, rgba(255, 255, 255, 0.5)),
    
    /* 3. Characters: "I" (right) and "O" (left) */
    linear-gradient(white, white), /* "I" */
    radial-gradient(circle, transparent 50%, white 52%, white 70%, transparent 72%), /* "O" */
    
    /* 4. Dots Pattern */
    radial-gradient(transparent 30%, rgba(101, 0, 0, 0.7) 70%),
    
    /* 5. Light: Radial glow (Initially hidden/transparent via size or color) */
    radial-gradient(circle at 75% 50%, #ffc97e, #ff1818 40%, transparent 70%),
    
    /* 6. Base Gradient */
    linear-gradient(90deg, #980000 0%, #6f0000 30%, #6f0000 70%, #980000 100%);

  background-position: 
    0 0,                    /* Shadow */
    50% 50%, 50% 50%,       /* Shine */
    80% 50%, 20% 50%,       /* "I", "O" */
    0 0,                    /* Dots */
    50% 50%,                /* Light */
    0 0;                    /* Base */

  background-size: 
    100% 100%,              /* Shadow */
    97% 97%, 97% 97%,       /* Shine */
    5% 20%, 20% 40%,        /* Characters */
    10px 10px,              /* Dots */
    0% 0%,                  /* Light: Effectively hidden */
    100% 100%;              /* Base */

  background-repeat: no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, repeat, no-repeat, no-repeat;
  
  /* Outer box-shadow to replace the frame's job slightly, though rotating */
  box-shadow: -5px 0 10px 0px rgba(0,0,0,0.5);
}

/* Left Face */
.switch::before {
  content: "";
  position: absolute;
  left: 2px;
  top: 0;
  bottom: 0;
  width: 50px;
  /* height: 100%; -> Changed to adjust for rounded corners */
  transform-origin: left;
  transform: rotateY(90deg);
  background: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.8) 10%,
        rgba(255, 255, 255, 0.3) 30%,
        #650000 75%,
        #320000
      )
      50% 50%/97% 97% no-repeat,
    #b10000;
}

/* Right Face */
.switch::after {
  content: "";
  position: absolute;
  right: 2px;
  top: 0;
  bottom: 0;
  width: 50px;
  /* height: 100%; -> Changed to adjust for rounded corners */
  transform-origin: right;
  transform: rotateY(-90deg);
  background-image: linear-gradient(90deg, #650000, #320000);
  /* Removed box-shadow artifact */
}

/* Checked State */
.switch:checked {
  transform: perspective(700px) translateZ(20px) rotateY(25deg);
  box-shadow: -10px 0 20px #ff1818;
  
  background-image:
    /* 1. Shadow: Right side dark (Right is recessed/away) */
    linear-gradient(to right, transparent 70%, rgba(0, 0, 0, 0.8)),
    /* 2. Shine: Unchanged */
    linear-gradient(to bottom, white, transparent 3%),
    linear-gradient(to right, rgba(255, 255, 255, 0.5), transparent 50%, transparent 80%, rgba(255, 255, 255, 0.5)),
    /* 3. Characters: Unchanged */
    linear-gradient(white, white),
    radial-gradient(circle, transparent 50%, white 52%, white 70%, transparent 72%),
    /* 4. Dots: Unchanged */
    radial-gradient(transparent 30%, rgba(101, 0, 0, 0.7) 70%),
    /* 5. Light: Now visible */
    radial-gradient(circle at 75% 50%, #ffc97e, #ff1818 40%, transparent 70%),
    /* 6. Base: Unchanged */
    linear-gradient(90deg, #980000 0%, #6f0000 30%, #6f0000 70%, #980000 100%);

  background-size: 
    100% 100%,
    97% 97%, 97% 97%,
    5% 20%, 20% 40%,
    10px 10px,
    100% 100%, /* Light expands to full */
    100% 100%;
}
</style>
