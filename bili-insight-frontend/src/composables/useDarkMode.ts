import { ref, watch } from 'vue'

const isDark = ref(localStorage.getItem('dark-mode') === 'true')

// Apply initial state without animation
if (isDark.value) {
  document.documentElement.classList.add('dark')
}

/**
 * Toggle dark mode with a circular animation originating from the click position.
 *
 * - Enabling dark:  new dark snapshot expands from click point  (dark circle grows)
 * - Disabling dark: old dark snapshot shrinks into click point  (dark circle shrinks,
 *                   revealing the light page underneath)
 *
 * For the shrink direction the OLD snapshot must sit on TOP so the dark layer
 * visually collapses inward — achieved by swapping z-index via a data attribute.
 */
function toggleDark(event?: MouseEvent) {
  const next = !isDark.value

  const x = event?.clientX ?? window.innerWidth / 2
  const y = event?.clientY ?? window.innerHeight / 2
  const endRadius = Math.hypot(
    Math.max(x, window.innerWidth - x),
    Math.max(y, window.innerHeight - y),
  )

  if (!('startViewTransition' in document)) {
    isDark.value = next
    ;(document as Document).documentElement.classList.toggle('dark', next)
    return
  }

  // Signal which direction we're going so CSS can set the right z-index
  document.documentElement.dataset.darkTransition = next ? 'enter' : 'leave'

  const transition = (document as any).startViewTransition(() => {
    isDark.value = next
    document.documentElement.classList.toggle('dark', next)
  })

  transition.ready.then(() => {
    if (next) {
      // Dark ON: new (dark) layer expands from click point
      document.documentElement.animate(
        {
          clipPath: [
            `circle(0px at ${x}px ${y}px)`,
            `circle(${endRadius}px at ${x}px ${y}px)`,
          ],
        },
        {
          duration: 500,
          easing: 'ease-in-out',
          pseudoElement: '::view-transition-new(root)',
        },
      )
    } else {
      // Dark OFF: old (dark) layer shrinks into click point — dark collapses from edges
      document.documentElement.animate(
        {
          clipPath: [
            `circle(${endRadius}px at ${x}px ${y}px)`,
            `circle(0px at ${x}px ${y}px)`,
          ],
        },
        {
          duration: 500,
          easing: 'ease-in-out',
          fill: 'forwards',
          pseudoElement: '::view-transition-old(root)',
        },
      )
    }
  })

  transition.finished.then(() => {
    delete document.documentElement.dataset.darkTransition
  })
}

watch(isDark, (val) => {
  localStorage.setItem('dark-mode', String(val))
})

export function useDarkMode() {
  return { isDark, toggleDark }
}
