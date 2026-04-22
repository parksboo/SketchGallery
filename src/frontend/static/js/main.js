(function () {
  function showToast(message, level) {
    if (!message) {
      return;
    }

    const toast = document.createElement('div');
    toast.className = 'toast ' + (level === 'error' ? 'error' : 'success');
    toast.textContent = message;
    document.body.appendChild(toast);

    window.setTimeout(function () {
      toast.classList.add('show');
    }, 20);

    window.setTimeout(function () {
      toast.classList.remove('show');
      window.setTimeout(function () {
        toast.remove();
      }, 220);
    }, 2800);
  }

  const params = new URLSearchParams(window.location.search);
  const toastMsg = params.get('toast');
  const toastLevel = params.get('toast_level') || 'success';
  if (toastMsg) {
    showToast(toastMsg, toastLevel);
    params.delete('toast');
    params.delete('toast_level');
    const cleanQuery = params.toString();
    const cleanUrl = window.location.pathname + (cleanQuery ? ('?' + cleanQuery) : '') + window.location.hash;
    window.history.replaceState({}, '', cleanUrl);
  }

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

  const jobMatch = window.location.pathname.match(/^\/jobs\/([0-9a-f-]+)$/i);
  if (jobMatch) {
    const jobId = jobMatch[1];
    const badge = document.querySelector('.badge');

    if (badge && !['completed', 'failed'].includes(badge.textContent.trim().toLowerCase())) {
      const poll = window.setInterval(async function () {
        try {
          const response = await fetch('/api/v1/jobs/' + jobId, {
            headers: { 'Accept': 'application/json' }
          });

          if (!response.ok) {
            return;
          }

          const job = await response.json();
          const status = (job.status || '').toLowerCase();

          if (status === 'completed' || status === 'failed') {
            window.clearInterval(poll);
            window.location.reload();
          }
        } catch (err) {
          console.error('Job polling failed:', err);
        }
      }, 2000);
    }
  }

  const createForm = document.getElementById('create-form');
  if (!createForm) {
    return;
  }

  const fileInput = document.getElementById('sketch_file');
  const sketchKeyInput = document.getElementById('sketch_key');
  const sketchNameInput = document.getElementById('sketch_name');
  const submitBtn = document.getElementById('create-submit');
  const statusEl = document.getElementById('create-status');
  const signUrl = createForm.dataset.signUrl;

  function setStatus(msg, isError) {
    statusEl.textContent = msg || '';
    statusEl.style.color = isError ? '#991b1b' : '#374151';
  }

  async function requestSignedUpload(file) {
    const response = await fetch(signUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: file.name,
        content_type: file.type || 'image/png',
        purpose: 'sketches'
      })
    });

    if (!response.ok) {
      throw new Error('Failed to get signed URL: ' + (await response.text()));
    }

    return response.json();
  }

  async function uploadToGcs(uploadUrl, file) {
    const response = await fetch(uploadUrl, {
      method: 'PUT',
      headers: { 'Content-Type': 'image/png' },
      body: file
    });

    if (!response.ok) {
      throw new Error('GCS upload failed: ' + (await response.text()));
    }
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

    if (!signUrl) {
      setStatus('Signed upload endpoint is missing.', true);
      return;
    }

    try {
      submitBtn.disabled = true;
      setStatus('Requesting signed URL...', false);

      const signed = await requestSignedUpload(file);
      setStatus('Uploading PNG directly to GCS...', false);
      await uploadToGcs(signed.upload_url, file);

      sketchKeyInput.value = signed.object_key;
      sketchNameInput.value = file.name;

      setStatus('Upload complete. Creating job...', false);
      createForm.submit();
    } catch (err) {
      setStatus(err.message || 'Upload failed.', true);
      submitBtn.disabled = false;
    }
  });
})();
