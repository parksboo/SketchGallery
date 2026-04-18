(function () {
  const progress = document.querySelector('.progress-bar');
  if (progress) {
    const label = document.querySelector('.badge');
    if (label && label.textContent.trim() !== 'completed') {
      progress.animate(
        [
          { filter: 'saturate(100%)' },
          { filter: 'saturate(130%)' },
          { filter: 'saturate(100%)' }
        ],
        {
          duration: 1300,
          iterations: Infinity,
          easing: 'ease-in-out'
        }
      );
    }
  }

  if (window.location.pathname === '/gallery') {
    const key = 'museumScrollY';
    const savedY = sessionStorage.getItem(key);
    if (savedY !== null) {
      window.scrollTo(0, Number(savedY));
      sessionStorage.removeItem(key);
    }

    function preserveScrollOnNavigate(selector) {
      const links = document.querySelectorAll(selector);
      links.forEach((link) => {
        link.addEventListener('click', function () {
          sessionStorage.setItem(key, String(window.scrollY));
        });
      });
    }

    preserveScrollOnNavigate('.museum-thumb');
    preserveScrollOnNavigate('.museum-nav');
  }

  const createForm = document.getElementById('create-form');
  if (!createForm) {
    return;
  }

  const fileInput = document.getElementById('sketch_file');
  const jobIdInput = document.getElementById('job_id');
  const sketchKeyInput = document.getElementById('sketch_key');
  const sketchNameInput = document.getElementById('sketch_name');
  const submitBtn = document.getElementById('create-submit');
  const statusEl = document.getElementById('create-status');
  const uploadUrl = createForm.dataset.uploadUrl;

  function setStatus(msg, isError) {
    statusEl.textContent = msg || '';
    statusEl.style.color = isError ? '#991b1b' : '#374151';
  }

  createForm.addEventListener('submit', async function (event) {
    event.preventDefault();

    const file = fileInput.files && fileInput.files[0];
    if (!file) {
      setStatus('Please choose a PNG file.', true);
      return;
    }

    if (!file.name.toLowerCase().endsWith('.png')) {
      setStatus('Only PNG files are allowed.', true);
      return;
    }

    if (!uploadUrl) {
      setStatus('Dataplane upload URL is missing.', true);
      return;
    }

    try {
      submitBtn.disabled = true;
      setStatus('Uploading sketch to dataplane...', false);

      const fd = new FormData();
      fd.append('file', file);

      const uploadResp = await fetch(uploadUrl, {
        method: 'POST',
        body: fd
      });

      if (!uploadResp.ok) {
        const text = await uploadResp.text();
        throw new Error('Upload failed: ' + text);
      }

      const payload = await uploadResp.json();
      sketchKeyInput.value = payload.key;
      sketchNameInput.value = file.name;
      jobIdInput.value = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now());

      setStatus('Upload complete. Creating job...', false);
      createForm.submit();
    } catch (err) {
      setStatus(err.message || 'Failed to upload file.', true);
      submitBtn.disabled = false;
    }
  });
})();
