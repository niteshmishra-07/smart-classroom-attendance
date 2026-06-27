/* Sidebar toggle for mobile */
(function () {
  const burger = document.getElementById('hamburger');
  const sidebar = document.getElementById('sidebar');
  if (!burger || !sidebar) return;
  burger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
  // close when clicking a nav-item on mobile
  sidebar.querySelectorAll('.nav-item').forEach(a => {
    a.addEventListener('click', () => sidebar.classList.remove('open'));
  });
})();
