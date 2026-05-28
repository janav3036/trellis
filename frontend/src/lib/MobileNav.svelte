<script>
  import { onMount } from 'svelte';

  let currentPath = '/';

  onMount(() => {
    const update = () => {
      const hash = window.location.hash.replace(/^#/, '') || '/';
      currentPath = hash.split('?')[0];
    };
    update();
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  });

  const NAV = [
    { href: '/',        label: 'HME' },
    { href: '/music',   label: 'MUS' },
    { href: '/code',    label: 'COD' },
    { href: '/life',    label: 'LIF' },
    { href: '/weather', label: 'WTR' },
    { href: '/f1',      label: 'F1'  },
    { href: '/journal', label: 'JRN' },
    { href: '/market',  label: 'MKT' },
    { href: '/sky',     label: 'SKY' },
    { href: '/chat',    label: 'RAG' },
    { href: '/edit',    label: 'EDT' },
  ];
</script>

<nav class="mob-nav" aria-label="Main navigation">
  {#each NAV as item}
    <a
      href={`/#${item.href}`}
      class="nav-slot"
      class:on={currentPath === item.href}
      aria-current={currentPath === item.href ? 'page' : undefined}
    >{item.label}</a>
  {/each}
</nav>

<style>
  .mob-nav {
    display: none;
  }

  @media (max-width: 768px) {
    .mob-nav {
      display: flex;
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      z-index: 200;
      background: rgba(7, 6, 4, 0.96);
      backdrop-filter: blur(22px) saturate(1.5);
      -webkit-backdrop-filter: blur(22px) saturate(1.5);
      border-top: 1px solid rgba(255, 255, 255, 0.038);
    }

    .nav-slot {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      height: calc(40px + env(safe-area-inset-bottom, 0px));
      padding-bottom: env(safe-area-inset-bottom, 0px);
      font-family: 'DM Mono', 'SF Mono', 'Fira Code', ui-monospace, monospace;
      font-size: 7px;
      font-weight: 400;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      text-decoration: none;
      color: rgba(155, 140, 120, 0.26);
      transition: color 0.18s ease;
      position: relative;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }

    .nav-slot::before {
      content: '';
      position: absolute;
      top: 0;
      left: 18%;
      right: 18%;
      height: 1.5px;
      background: var(--accent, #c8813a);
      opacity: 0;
      transition: opacity 0.18s ease;
      border-radius: 0 0 2px 2px;
    }

    .nav-slot.on {
      color: var(--accent, #c8813a);
    }

    .nav-slot.on::before {
      opacity: 1;
    }
  }
</style>
