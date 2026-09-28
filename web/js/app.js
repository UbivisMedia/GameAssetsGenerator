/**
 * GameAssetGenerator Frontend Application Logic (English)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global State
  const state = {
    config: {},
    categories: [],
    perspectives: [],
    resolutions: {},
    animations: [],
    styles: [],
    selectedPerspective: 'side_view',
    selectedAction: 'walk',
    selectedSteps: 4,
    currentAsset: null,
    isPlaying: false,
    currentFrameIndex: 0,
    animationInterval: null,
    fps: 8,
    zoomLevel: '4x',
    characters: [],
    selectedCharacter: null,
    selectedDirection: 'S',
    directionMode: '8_directional',
    mirrorSymmetry: true,
    activePreviewDirection: 'S',
    onionSkinEnabled: false,
    normalMapPreview: false,
    currentMapType: 'diffuse',
    directionalFramesMap: null
  };

  // DOM Elements
  const statusComfyUI = document.getElementById('status-comfyui');
  const statusLMStudio = document.getElementById('status-lmstudio');
  const btnRefreshStatus = document.getElementById('btn-refresh-status');
  
  const projectSelect = document.getElementById('project-select');
  const rubrikSelect = document.getElementById('rubrik-select');
  const btnNewProject = document.getElementById('btn-new-project');
  const assetNameInput = document.getElementById('asset-name');

  // Character Grouping Elements
  const characterGroupSection = document.getElementById('character-group-section');
  const characterSelect = document.getElementById('character-select');
  const btnNewCharacter = document.getElementById('btn-new-character');
  const characterAnchorBox = document.getElementById('character-anchor-box');
  const characterMasterThumb = document.getElementById('character-master-thumb');
  const characterAnchorName = document.getElementById('character-anchor-name');
  const characterAnchorPerspective = document.getElementById('character-anchor-perspective');
  const characterAnchorAnims = document.getElementById('character-anchor-anims');
  const checkUseCharacterRef = document.getElementById('check-use-character-ref');

  const modalNewCharacter = document.getElementById('modal-new-character');
  const newCharacterName = document.getElementById('new-character-name');
  const newCharacterPrompt = document.getElementById('new-character-prompt');
  const btnModalCharCancel = document.getElementById('btn-modal-char-cancel');
  const btnModalCharConfirm = document.getElementById('btn-modal-char-confirm');

  const perspectiveCards = document.querySelectorAll('.perspective-card');
  const perspectiveDesc = document.getElementById('perspective-description');

  // Direction & Compass Rosette Elements
  const directionSection = document.getElementById('direction-section');
  const directionModeBadge = document.getElementById('direction-mode-badge');
  const dirModeBtns = document.querySelectorAll('.dir-mode-btn');
  const compassNodes = document.querySelectorAll('.compass-node');
  const compassActiveDirLabel = document.getElementById('compass-active-dir-label');
  const compassActiveDirDesc = document.getElementById('compass-active-dir-desc');
  const checkMirrorSymmetry = document.getElementById('check-mirror-symmetry');


  const resPresetsContainer = document.getElementById('resolution-presets');
  const widthInput = document.getElementById('width-input');
  const heightInput = document.getElementById('height-input');
  const scalingMode = document.getElementById('scaling-mode');

  const actionButtonsContainer = document.getElementById('action-buttons');
  const stepsSlider = document.getElementById('steps-slider');
  const stepsValDisplay = document.getElementById('steps-val-display');
  const fpsInput = document.getElementById('fps-input');
  const stepsBreakdownList = document.getElementById('steps-breakdown-list');
  const btnLMPlan = document.getElementById('btn-lm-plan');

  const styleSelect = document.getElementById('style-select');
  const promptInput = document.getElementById('prompt-input');
  const negativePrompt = document.getElementById('negative-prompt');
  const btnEnhancePrompt = document.getElementById('btn-enhance-prompt');
  const seedInput = document.getElementById('seed-input');
  const comfySteps = document.getElementById('comfy-steps');
  const cfgInput = document.getElementById('cfg-input');
  const checkRembg = document.getElementById('check-rembg');

  // AI Models & Engine Elements
  const checkpointSelect = document.getElementById('checkpoint-select');
  const checkpointLabel = document.getElementById('checkpoint-label');
  const checkpointRoleHint = document.getElementById('checkpoint-role-hint');
  const checkpointBadge = document.getElementById('checkpoint-badge');
  const loraSelect = document.getElementById('lora-select');
  const loraStrengthSlider = document.getElementById('lora-strength-slider');
  const loraStrengthVal = document.getElementById('lora-strength-val');
  const unetSelect = document.getElementById('unet-select');
  const unetActiveBadge = document.getElementById('unet-active-badge');
  const vaeSelect = document.getElementById('vae-select');
  const samplerSelect = document.getElementById('sampler-select');
  const schedulerSelect = document.getElementById('scheduler-select');
  const btnRefreshModels = document.getElementById('btn-refresh-models');
  const lmModelSelect = document.getElementById('lm-model-select');

  const btnGenerate = document.getElementById('btn-generate');
  const btnGenerateMock = document.getElementById('btn-generate-mock');

  // Preview Player Elements
  const activeFrameImg = document.getElementById('active-frame-img');
  const emptyState = document.getElementById('empty-state');
  const spriteContainer = document.getElementById('sprite-container');
  const spriteViewport = document.getElementById('sprite-viewport');
  const btnPlayPause = document.getElementById('btn-play-pause');
  const btnStepPrev = document.getElementById('btn-step-prev');
  const btnStepNext = document.getElementById('btn-step-next');
  const currentFrameIdxSpan = document.getElementById('current-frame-idx');
  const totalFramesCountSpan = document.getElementById('total-frames-count');
  const playerFpsSlider = document.getElementById('player-fps-slider');
  const playerFpsDisplay = document.getElementById('player-fps-display');
  const zoomBtns = document.querySelectorAll('.zoom-btn');
  const btnToggleGrid = document.getElementById('btn-toggle-grid');
  const btnToggleOnion = document.getElementById('btn-toggle-onion');
  const btnToggleNormal = document.getElementById('btn-toggle-normal');
  const onionFramePrev = document.getElementById('onion-frame-prev');
  const onionFrameNext = document.getElementById('onion-frame-next');
  const playerDirectionBar = document.getElementById('player-direction-bar');
  const playerDirButtons = document.getElementById('player-dir-buttons');

  // Export & Tabs
  const exportCard = document.getElementById('export-card');
  const downloadSpritesheet = document.getElementById('download-spritesheet');
  const downloadNormal = document.getElementById('download-normal');
  const downloadDepth = document.getElementById('download-depth');
  const downloadGif = document.getElementById('download-gif');
  const downloadWebp = document.getElementById('download-webp');
  const downloadMetadata = document.getElementById('download-metadata');
  const outputSavedPath = document.getElementById('output-saved-path');

  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  // Spritesheet Viewer & Chroma Tool Elements
  const mapPillBtns = document.querySelectorAll('.map-pill-btn');
  const chromaColorPicker = document.getElementById('chroma-color-picker');
  const btnEyedropper = document.getElementById('btn-eyedropper');
  const chromaToleranceSlider = document.getElementById('chroma-tolerance-slider');
  const chromaTolVal = document.getElementById('chroma-tol-val');
  const btnApplyChroma = document.getElementById('btn-apply-chroma');
  const btnRebakeMaps = document.getElementById('btn-rebake-maps');
  const spritesheetFullImg = document.getElementById('spritesheet-full-img');
  const spritesheetEmpty = document.getElementById('spritesheet-empty');
  const framesStripGrid = document.getElementById('frames-strip-grid');
  const galleryGrid = document.getElementById('gallery-grid');
  const galleryRubrikFilter = document.getElementById('gallery-rubrik-filter');

  // Toast & Modal
  const toast = document.getElementById('toast');
  const modalNewProject = document.getElementById('modal-new-project');
  const newProjectInput = document.getElementById('new-project-input');
  const btnModalCancel = document.getElementById('btn-modal-cancel');
  const btnModalConfirm = document.getElementById('btn-modal-confirm');

  // --- Helper Functions ---
  function showToast(message, duration = 3000) {
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
  }

  // --- Service Status Check ---
  async function checkServices() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();

      // ComfyUI Status
      if (data.comfyui && data.comfyui.online) {
        statusComfyUI.className = 'status-pill status-online';
        statusComfyUI.querySelector('.status-label').textContent = 'ComfyUI: Online';
      } else {
        statusComfyUI.className = 'status-pill status-offline';
        statusComfyUI.querySelector('.status-label').textContent = 'ComfyUI: Offline (Mock Available)';
      }

      // LM Studio Status
      if (data.lm_studio && data.lm_studio.online) {
        if (data.lm_studio.has_loaded_model) {
          statusLMStudio.className = 'status-pill status-online';
          const modelName = data.lm_studio.loaded_model ? data.lm_studio.loaded_model.split('/').pop() : 'Ready';
          statusLMStudio.querySelector('.status-label').textContent = `LM Studio: ${modelName}`;
        } else {
          statusLMStudio.className = 'status-pill status-offline';
          statusLMStudio.querySelector('.status-label').textContent = 'LM Studio: No Model Loaded';
        }
      } else {
        statusLMStudio.className = 'status-pill status-offline';
        statusLMStudio.querySelector('.status-label').textContent = 'LM Studio: Offline';
      }
    } catch (e) {
      statusComfyUI.className = 'status-pill status-offline';
      statusLMStudio.className = 'status-pill status-offline';
    }
  }

  // --- Model Grouping & Loading ---
  function groupItemsByFolder(items, selectElem, emptyLabel = null) {
    if (!selectElem) return;
    selectElem.innerHTML = '';
    if (emptyLabel) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = emptyLabel;
      selectElem.appendChild(opt);
    }
    const groups = {};
    items.forEach(item => {
      let folder = 'Root';
      let name = item;
      if (item.includes('\\')) {
        const parts = item.split('\\');
        folder = parts.slice(0, -1).join(' / ');
        name = parts[parts.length - 1];
      } else if (item.includes('/')) {
        const parts = item.split('/');
        folder = parts.slice(0, -1).join(' / ');
        name = parts[parts.length - 1];
      }
      if (!groups[folder]) groups[folder] = [];
      groups[folder].push({ value: item, label: name });
    });

    Object.keys(groups).sort().forEach(folder => {
      const optgroup = document.createElement('optgroup');
      optgroup.label = folder;
      groups[folder].forEach(g => {
        const opt = document.createElement('option');
        opt.value = g.value;
        opt.textContent = g.label;
        optgroup.appendChild(opt);
      });
      selectElem.appendChild(optgroup);
    });
  }

  async function loadModels() {
    if (!checkpointSelect) return;
    try {
      if (checkpointBadge) checkpointBadge.textContent = 'Fetching models...';
      const res = await fetch('/api/comfy/models');
      const data = await res.json();
      state.models = data;

      // 1. Checkpoints
      const ckpts = data.checkpoints || [];
      if (checkpointBadge) checkpointBadge.textContent = `${ckpts.length} available`;
      groupItemsByFolder(ckpts, checkpointSelect);
      const savedCkpt = localStorage.getItem('gag_checkpoint');
      if (savedCkpt && ckpts.includes(savedCkpt)) {
        checkpointSelect.value = savedCkpt;
      } else if (ckpts.length > 0) {
        const imageCkpts = ckpts.filter(c => !c.toLowerCase().includes('audio') && !c.toLowerCase().includes('yue'));
        const candidates = imageCkpts.length > 0 ? imageCkpts : ckpts;
        const pref = candidates.find(c => c.toLowerCase().includes('sd 1.5') || c.toLowerCase().includes('anime')) || candidates[0];
        checkpointSelect.value = pref;
      }

      // 2. LoRAs
      const loras = data.loras || [];
      groupItemsByFolder(loras, loraSelect, '-- None / No LoRA --');
      const savedLora = localStorage.getItem('gag_lora');
      if (savedLora && loras.includes(savedLora)) {
        loraSelect.value = savedLora;
      }

      // 3. UNets
      const unets = data.unets || [];
      groupItemsByFolder(unets, unetSelect, '-- None (Use Checkpoint UNet) --');
      const savedUnet = localStorage.getItem('gag_unet');
      if (savedUnet && unets.includes(savedUnet)) {
        unetSelect.value = savedUnet;
      }
      updateModelRoleUI();

      // 4. VAEs
      const vaes = data.vaes || [];
      groupItemsByFolder(vaes, vaeSelect, '-- Baked-in VAE --');

      // 5. Samplers & Schedulers
      if (samplerSelect) {
        samplerSelect.innerHTML = '';
        (data.samplers || ['euler_ancestral', 'euler', 'dpmpp_2m']).forEach(s => {
          const opt = document.createElement('option');
          opt.value = s;
          opt.textContent = s;
          if (s === 'euler_ancestral') opt.selected = true;
          samplerSelect.appendChild(opt);
        });
      }

      if (schedulerSelect) {
        schedulerSelect.innerHTML = '';
        (data.schedulers || ['karras', 'normal', 'sgm_uniform']).forEach(s => {
          const opt = document.createElement('option');
          opt.value = s;
          opt.textContent = s;
          if (s === 'karras') opt.selected = true;
          schedulerSelect.appendChild(opt);
        });
      }
    } catch (e) {
      if (checkpointBadge) checkpointBadge.textContent = 'Offline';
      console.error('Failed to load ComfyUI models:', e);
    }
  }

  function updateModelRoleUI() {
    const hasUnet = unetSelect && unetSelect.value && unetSelect.value.trim() !== '';
    const isAnima = hasUnet && unetSelect.value.toLowerCase().includes('anima');

    if (isAnima) {
      if (unetActiveBadge) {
        unetActiveBadge.style.display = 'inline-block';
        unetActiveBadge.textContent = 'Active Anima Engine (Qwen + Wan VAE)';
      }
      if (checkpointLabel) {
        checkpointLabel.textContent = 'Diffusion Checkpoint (Auto-Bypassed)';
      }
      if (checkpointRoleHint) {
        checkpointRoleHint.textContent = 'Anima uses its dedicated Qwen 0.6B text encoder and Wan 2.1 VAE automatically. Checkpoint is bypassed.';
      }
      if (checkpointBadge) {
        checkpointBadge.textContent = 'Bypassed (DiT Mode)';
      }
    } else if (hasUnet) {
      if (unetActiveBadge) {
        unetActiveBadge.style.display = 'inline-block';
        unetActiveBadge.textContent = 'Active Generative Engine';
      }
      if (checkpointLabel) {
        checkpointLabel.textContent = 'CLIP & VAE Provider Checkpoint';
      }
      if (checkpointRoleHint) {
        checkpointRoleHint.textContent = 'Generative model is overridden by Custom UNet below. This Checkpoint provides the CLIP text encoder and VAE decoder.';
      }
      if (checkpointBadge) {
        checkpointBadge.textContent = 'CLIP + VAE Source';
      }
    } else {
      if (unetActiveBadge) {
        unetActiveBadge.style.display = 'none';
      }
      if (checkpointLabel) {
        checkpointLabel.textContent = 'Diffusion Checkpoint (Base Model)';
      }
      if (checkpointRoleHint) {
        checkpointRoleHint.textContent = 'Standard all-in-one base model (Generative UNet + Text Encoder CLIP + VAE).';
      }
      if (checkpointBadge) {
        const count = (state.models && state.models.checkpoints) ? state.models.checkpoints.length : 0;
        checkpointBadge.textContent = `${count} available`;
      }
    }
  }

  if (unetSelect) {
    unetSelect.addEventListener('change', () => {
      if (unetSelect.value) {
        localStorage.setItem('gag_unet', unetSelect.value);
      } else {
        localStorage.removeItem('gag_unet');
      }
      updateModelRoleUI();
    });
  }

  async function loadLMModels() {
    if (!lmModelSelect) return;
    try {
      const res = await fetch('/api/lm/models');
      const data = await res.json();
      lmModelSelect.innerHTML = '';
      const list = data.models || [];
      list.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = `${m.is_loaded ? '● ' : '○ '}${m.name} ${m.is_loaded ? '(Active)' : ''}`;
        if (m.is_loaded) opt.selected = true;
        lmModelSelect.appendChild(opt);
      });
    } catch (e) {
      console.error('Failed to load LM Studio models:', e);
    }
  }

  // --- Load Config & Populate UI ---
  async function loadConfig() {
    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      state.config = data.config;
      state.categories = data.categories || [];
      state.perspectives = data.perspectives || [];
      state.resolutions = data.resolutions || {};
      state.animations = data.animations || [];
      state.styles = data.styles || [];

      populateCategories();
      populateStyles();
      populateResolutionPresets();
      populateActionButtons();
      updatePerspectiveUI();
      updateCompassUI();
      updateStepBreakdownUI();
      await loadProjects();
      await loadModels();
      await loadLMModels();
    } catch (e) {
      console.error('Config load failed:', e);
      showToast('Error loading configuration');
    }
  }

  function populateCategories() {
    rubrikSelect.innerHTML = '';
    galleryRubrikFilter.innerHTML = '<option value="">All Categories</option>';
    state.categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat.id;
      opt.textContent = `${cat.name} (${cat.id})`;
      rubrikSelect.appendChild(opt);

      const filterOpt = document.createElement('option');
      filterOpt.value = cat.id;
      filterOpt.textContent = cat.name;
      galleryRubrikFilter.appendChild(filterOpt);
    });
  }

  function populateStyles() {
    styleSelect.innerHTML = '';
    state.styles.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.name;
      styleSelect.appendChild(opt);
    });
  }

  function populateResolutionPresets() {
    resPresetsContainer.innerHTML = '';
    const presets = state.resolutions.presets || [];
    presets.forEach((p) => {
      const btn = document.createElement('button');
      btn.className = `preset-chip ${p.width === 64 ? 'active' : ''}`;
      btn.textContent = `${p.width}x${p.height}`;
      btn.dataset.w = p.width;
      btn.dataset.h = p.height;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        widthInput.value = p.width;
        heightInput.value = p.height;
      });
      resPresetsContainer.appendChild(btn);
    });
  }

  function populateActionButtons() {
    actionButtonsContainer.innerHTML = '';
    state.animations.forEach(act => {
      const btn = document.createElement('button');
      btn.className = `action-chip ${act.id === state.selectedAction ? 'active' : ''}`;
      btn.textContent = act.name.split(' (')[0];
      btn.dataset.action = act.id;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.action-chip').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        state.selectedAction = act.id;
        if (act.default_steps) {
          stepsSlider.value = act.default_steps;
          stepsValDisplay.textContent = act.default_steps;
          state.selectedSteps = act.default_steps;
        }
        if (act.recommended_fps) {
          fpsInput.value = act.recommended_fps;
          playerFpsSlider.value = act.recommended_fps;
          playerFpsDisplay.textContent = act.recommended_fps;
          state.fps = act.recommended_fps;
        }
        if (state.selectedCharacter) {
          assetNameInput.value = `${state.selectedCharacter.character_id}_${state.selectedAction}`;
        }
        updateStepBreakdownUI();
      });
      actionButtonsContainer.appendChild(btn);
    });
  }

  const DIR_DESCRIPTIONS = {
    'N': 'Away (0°)',
    'NE': 'Right-Up (45°)',
    'E': 'Right (90°)',
    'SE': 'Right-Down (135°)',
    'S': 'Front (180°)',
    'SW': 'Left-Down (225°)',
    'W': 'Left (270°)',
    'NW': 'Left-Up (315°)'
  };

  function updatePerspectiveUI() {
    perspectiveCards.forEach(card => {
      const id = card.dataset.perspective;
      if (id === state.selectedPerspective) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });

    const activePersp = state.perspectives.find(p => p.id === state.selectedPerspective);
    if (activePersp && perspectiveDesc) {
      perspectiveDesc.textContent = activePersp.description;
    }

    if (directionSection) {
      if (state.selectedPerspective === 'top_down' || state.selectedPerspective === 'isometric') {
        directionSection.style.display = 'block';
      } else {
        directionSection.style.display = 'none';
      }
    }
  }

  function updateCompassUI() {
    if (!compassNodes.length) return;

    dirModeBtns.forEach(btn => {
      if (btn.dataset.mode === state.directionMode) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    compassNodes.forEach(node => {
      const d = node.dataset.dir;
      node.classList.remove('active', 'mirrored');

      if (state.directionMode === 'single') {
        if (d === state.selectedDirection) {
          node.classList.add('active');
        }
      } else if (state.directionMode === '4_cardinal') {
        if (['S', 'W', 'N', 'E'].includes(d)) {
          node.classList.add('active');
          if (state.mirrorSymmetry && d === 'E') node.classList.add('mirrored');
        }
      } else if (state.directionMode === 'isometric_4') {
        if (['SE', 'SW', 'NW', 'NE'].includes(d)) {
          node.classList.add('active');
          if (state.mirrorSymmetry && ['NE', 'SE'].includes(d)) node.classList.add('mirrored');
        }
      } else if (state.directionMode === '8_directional') {
        node.classList.add('active');
        if (state.mirrorSymmetry && ['E', 'SE', 'NE'].includes(d)) node.classList.add('mirrored');
      }
    });

    if (directionModeBadge) {
      if (state.directionMode === 'single') directionModeBadge.textContent = 'Single Angle';
      else if (state.directionMode === '4_cardinal') directionModeBadge.textContent = '4-Way Cardinal';
      else if (state.directionMode === 'isometric_4') directionModeBadge.textContent = '4-Way Isometric';
      else directionModeBadge.textContent = '8-Way Suite';
    }

    if (compassActiveDirLabel) {
      if (state.directionMode === 'single') {
        compassActiveDirLabel.textContent = state.selectedDirection;
        compassActiveDirDesc.textContent = DIR_DESCRIPTIONS[state.selectedDirection] || '';
      } else if (state.directionMode === '4_cardinal') {
        compassActiveDirLabel.textContent = '4-Way';
        compassActiveDirDesc.textContent = 'N, E, S, W';
      } else if (state.directionMode === 'isometric_4') {
        compassActiveDirLabel.textContent = 'Iso 4';
        compassActiveDirDesc.textContent = 'SE, SW, NW, NE';
      } else {
        compassActiveDirLabel.textContent = '8-Way';
        compassActiveDirDesc.textContent = 'Full 360°';
      }
    }
  }

  dirModeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      state.directionMode = btn.dataset.mode;
      updateCompassUI();
    });
  });

  compassNodes.forEach(node => {
    node.addEventListener('click', () => {
      const d = node.dataset.dir;
      state.selectedDirection = d;
      state.directionMode = 'single';
      updateCompassUI();
    });
  });

  if (checkMirrorSymmetry) {
    checkMirrorSymmetry.addEventListener('change', (e) => {
      state.mirrorSymmetry = e.target.checked;
      updateCompassUI();
    });
  }

  perspectiveCards.forEach(card => {
    card.addEventListener('click', () => {
      state.selectedPerspective = card.dataset.perspective;
      updatePerspectiveUI();
      updateStepBreakdownUI();

      if (state.selectedPerspective === 'portrait') {
        if (resolutionSelect && (resolutionSelect.value === '64x64' || resolutionSelect.value === '32x32' || resolutionSelect.value === '16x16')) {
          const portraitOpt = Array.from(resolutionSelect.options).find(opt => opt.value === '512x768');
          if (portraitOpt) {
            resolutionSelect.value = '512x768';
            widthInput.value = 512;
            heightInput.value = 768;
          }
        }
      }
    });
  });

  stepsSlider.addEventListener('input', (e) => {
    state.selectedSteps = parseInt(e.target.value, 10);
    stepsValDisplay.textContent = state.selectedSteps;
    updateStepBreakdownUI();
  });

  function updateStepBreakdownUI() {
    stepsBreakdownList.innerHTML = '';
    const act = state.animations.find(a => a.id === state.selectedAction);
    const stepsCount = state.selectedSteps;

    const templates = (act && act.step_descriptions && act.step_descriptions[String(stepsCount)]) || [];

    for (let i = 0; i < stepsCount; i++) {
      const row = document.createElement('div');
      row.className = 'step-row';
      const desc = templates[i] || `Phase ${i + 1} (${state.selectedAction} ${state.selectedPerspective})`;
      row.innerHTML = `
        <span class="step-num">#${i + 1}</span>
        <span class="step-title">${desc}</span>
      `;
      stepsBreakdownList.appendChild(row);
    }
  }

  // --- Project & Character Loading & Creation ---
  async function loadProjects() {
    try {
      const res = await fetch('/api/projects');
      const data = await res.json();
      projectSelect.innerHTML = '';
      const list = data.projects || [];
      if (list.length === 0) {
        const defaultOpt = document.createElement('option');
        defaultOpt.value = 'MyGame';
        defaultOpt.textContent = 'MyGame';
        projectSelect.appendChild(defaultOpt);
      } else {
        list.forEach(p => {
          const opt = document.createElement('option');
          opt.value = p.name;
          opt.textContent = p.name;
          projectSelect.appendChild(opt);
        });
      }
      await loadCharacters();
    } catch (e) {
      console.error('Projects load failed:', e);
    }
  }

  async function loadCharacters() {
    const proj = projectSelect.value || 'MyGame';
    try {
      const res = await fetch(`/api/characters?project=${encodeURIComponent(proj)}`);
      const data = await res.json();
      state.characters = data.characters || [];
      characterSelect.innerHTML = '<option value="">-- Standalone Asset / Auto-Create --</option>';
      state.characters.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.character_id;
        opt.textContent = `${c.name} (${c.animations_count} anims)`;
        characterSelect.appendChild(opt);
      });
      updateCharacterUI();
    } catch (e) {
      console.error('Characters load failed:', e);
    }
  }

  function updateCharacterUI() {
    const charId = characterSelect.value;
    if (!charId) {
      characterAnchorBox.style.display = 'none';
      state.selectedCharacter = null;
      return;
    }

    const c = state.characters.find(item => item.character_id === charId);
    if (!c) {
      characterAnchorBox.style.display = 'none';
      state.selectedCharacter = null;
      return;
    }

    state.selectedCharacter = c;
    characterAnchorBox.style.display = 'flex';
    characterAnchorName.textContent = c.name;
    characterAnchorPerspective.textContent = c.perspective.toUpperCase();
    characterAnchorAnims.textContent = `${c.animations_count} Animations`;

    if (c.has_master_reference && c.master_reference_url) {
      characterMasterThumb.innerHTML = `<img src="${c.master_reference_url}?t=${Date.now()}" alt="${c.name}">`;
    } else {
      characterMasterThumb.innerHTML = `<span style="font-size:20px;">👤</span>`;
    }

    // Auto sync perspective with character's baseline
    if (c.perspective) {
      state.selectedPerspective = c.perspective;
      updatePerspectiveUI();
    }

    // Pre-fill prompt if empty
    if (!promptInput.value.trim() && c.base_prompt) {
      promptInput.value = c.base_prompt;
    }

    // Auto-update asset name
    assetNameInput.value = `${c.character_id}_${state.selectedAction}`;
  }

  characterSelect.addEventListener('change', updateCharacterUI);
  projectSelect.addEventListener('change', async () => {
    await loadCharacters();
  });

  rubrikSelect.addEventListener('change', () => {
    if (rubrikSelect.value === 'characters') {
      characterGroupSection.style.display = 'block';
    } else {
      characterGroupSection.style.display = 'none';
    }
  });

  btnNewProject.addEventListener('click', () => {
    modalNewProject.style.display = 'flex';
    newProjectInput.focus();
  });

  btnModalCancel.addEventListener('click', () => {
    modalNewProject.style.display = 'none';
  });

  btnModalConfirm.addEventListener('click', async () => {
    const name = newProjectInput.value.trim();
    if (!name) return;
    try {
      await fetch('/api/projects/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_name: name })
      });
      await loadProjects();
      projectSelect.value = name;
      modalNewProject.style.display = 'none';
      showToast(`Project '${name}' created!`);
    } catch (e) {
      showToast('Error creating project');
    }
  });

  // Modal Character Creation
  btnNewCharacter.addEventListener('click', () => {
    modalNewCharacter.style.display = 'flex';
    newCharacterName.focus();
  });

  btnModalCharCancel.addEventListener('click', () => {
    modalNewCharacter.style.display = 'none';
  });

  btnModalCharConfirm.addEventListener('click', async () => {
    const name = newCharacterName.value.trim();
    if (!name) return;
    const basePrompt = newCharacterPrompt.value.trim();

    try {
      const res = await fetch('/api/characters/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectSelect.value || 'MyGame',
          name: name,
          base_prompt: basePrompt,
          perspective: state.selectedPerspective,
          style_id: styleSelect.value
        })
      });
      const data = await res.json();
      await loadCharacters();
      if (data.character) {
        characterSelect.value = data.character.character_id;
        updateCharacterUI();
      }
      modalNewCharacter.style.display = 'none';
      newCharacterName.value = '';
      newCharacterPrompt.value = '';
      showToast(`Character '${name}' created!`);
    } catch (e) {
      showToast('Error creating character');
    }
  });


  // --- AI Actions (LM Studio) ---
  btnEnhancePrompt.addEventListener('click', async () => {
    const userPrompt = promptInput.value.trim();
    if (!userPrompt) {
      showToast('Please enter an asset description first!');
      return;
    }
    btnEnhancePrompt.textContent = '⏳ Enhancing...';
    try {
      const res = await fetch('/api/lm/enhance-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_prompt: userPrompt,
          category: rubrikSelect.value,
          perspective: state.selectedPerspective,
          style_id: styleSelect.value
        })
      });
      const data = await res.json();
      promptInput.value = data.positive_prompt;
      if (data.negative_prompt) {
        negativePrompt.value = data.negative_prompt;
      }
      showToast('Prompt successfully enhanced by AI!');
    } catch (e) {
      showToast('Unable to reach LM Studio');
    } finally {
      btnEnhancePrompt.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg> Enhance with AI
      `;
    }
  });

  btnLMPlan.addEventListener('click', async () => {
    const assetName = assetNameInput.value.trim() || promptInput.value.trim() || 'Character';
    btnLMPlan.textContent = '⏳ Planning poses...';
    try {
      const res = await fetch('/api/lm/plan-animation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_name: assetName,
          action: state.selectedAction,
          steps_count: state.selectedSteps,
          perspective: state.selectedPerspective
        })
      });
      const data = await res.json();
      if (data.steps && data.steps.length > 0) {
        stepsBreakdownList.innerHTML = '';
        data.steps.forEach(s => {
          const row = document.createElement('div');
          row.className = 'step-row';
          row.innerHTML = `
            <span class="step-num">#${s.step}</span>
            <span class="step-title"><strong>${s.pose_title || ''}</strong> ${s.prompt_extension || ''}</span>
          `;
          stepsBreakdownList.appendChild(row);
        });
        showToast('Animation keyframes planned by AI!');
      }
    } catch (e) {
      showToast('Error planning animation keyframes');
    } finally {
      btnLMPlan.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path>
        </svg> AI Keyframe Plan (LM Studio)
      `;
    }
  });

  // --- Asset Generation ---
  async function triggerGeneration(isMock = false) {
    let assetName = assetNameInput.value.trim();
    if (!assetName) {
      assetName = `asset_${Date.now()}`;
      assetNameInput.value = assetName;
    }

    const promptText = promptInput.value.trim() || 'Heroic game character';

    const isCharCategory = (rubrikSelect.value === 'characters');
    const selectedCharId = isCharCategory ? characterSelect.value : null;

    const payload = {
      project_name: projectSelect.value || 'DefaultProject',
      rubrik: rubrikSelect.value || 'characters',
      asset_name: assetName,
      character_id: selectedCharId || null,
      character_name: (selectedCharId && state.selectedCharacter) ? state.selectedCharacter.name : null,
      use_character_reference: checkUseCharacterRef ? checkUseCharacterRef.checked : true,
      prompt: promptText,
      negative_prompt: negativePrompt.value.trim(),
      perspective: state.selectedPerspective,
      action: state.selectedAction,
      steps_count: state.selectedSteps,
      fps: parseInt(fpsInput.value, 10) || 8,
      width: parseInt(widthInput.value, 10) || 64,
      height: parseInt(heightInput.value, 10) || 64,
      scaling_mode: scalingMode.value,
      seed: parseInt(seedInput.value, 10) || -1,
      steps: parseInt(comfySteps.value, 10) || 25,
      cfg: parseFloat(cfgInput.value) || 7.5,
      remove_background: checkRembg.checked,
      mock_demo: isMock,
      checkpoint: checkpointSelect ? checkpointSelect.value : null,
      unet: unetSelect ? unetSelect.value : null,
      lora: loraSelect ? loraSelect.value : null,
      lora_strength: loraStrengthSlider ? parseFloat(loraStrengthSlider.value) : 1.0,
      vae: vaeSelect ? vaeSelect.value : null,
      sampler_name: samplerSelect ? samplerSelect.value : null,
      scheduler: schedulerSelect ? schedulerSelect.value : null,
      direction: state.directionMode === 'single' ? state.selectedDirection : state.directionMode,
      mirror_symmetry: checkMirrorSymmetry ? checkMirrorSymmetry.checked : true,
      chroma_color: chromaColorPicker ? chromaColorPicker.value : null,
      chroma_tolerance: chromaToleranceSlider ? parseInt(chromaToleranceSlider.value, 10) : 35
    };

    if (checkpointSelect && checkpointSelect.value) {
      localStorage.setItem('gag_checkpoint', checkpointSelect.value);
    }
    if (loraSelect && loraSelect.value) {
      localStorage.setItem('gag_lora', loraSelect.value);
    }

    btnGenerate.disabled = true;
    btnGenerateMock.disabled = true;
    btnGenerate.innerHTML = '⏳ Generating...';

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'success' && data.asset) {
        displayAsset(data.asset);
        await loadCharacters();
        showToast('Asset generated & saved successfully!');
      } else {
        showToast('Generation failed');
      }
    } catch (e) {
      console.error(e);
      showToast('Network or server error');
    } finally {
      btnGenerate.disabled = false;
      btnGenerateMock.disabled = false;
      btnGenerate.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg> Generate Asset
      `;
    }
  }

  // --- Model Control Listeners ---
  if (loraStrengthSlider && loraStrengthVal) {
    loraStrengthSlider.addEventListener('input', (e) => {
      loraStrengthVal.textContent = parseFloat(e.target.value).toFixed(2);
    });
  }

  if (btnRefreshModels) {
    btnRefreshModels.addEventListener('click', async () => {
      showToast('Refreshing ComfyUI & LM Studio models...');
      await loadModels();
      await loadLMModels();
      await checkServices();
      showToast('Models refreshed!');
    });
  }

  if (lmModelSelect) {
    lmModelSelect.addEventListener('change', async () => {
      const selectedModel = lmModelSelect.value;
      if (!selectedModel) return;
      showToast(`Loading LM Studio model: ${selectedModel}...`);
      try {
        const res = await fetch('/api/lm/load-model', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model_id: selectedModel })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('LM Studio model loaded successfully!');
          await checkServices();
          await loadLMModels();
        } else {
          showToast(`Failed to load model: ${data.message || 'error'}`);
        }
      } catch (e) {
        showToast('Error communicating with LM Studio');
      }
    });
  }

  btnGenerate.addEventListener('click', () => triggerGeneration(false));
  btnGenerateMock.addEventListener('click', () => triggerGeneration(true));

  // --- Helper to get currently active frames array ---
  function getActiveFramesList() {
    if (!state.currentAsset) return [];
    if (state.directionalFramesMap && state.directionalFramesMap[state.activePreviewDirection]) {
      return state.directionalFramesMap[state.activePreviewDirection];
    }
    return (state.currentAsset.paths && state.currentAsset.paths.frames) ? state.currentAsset.paths.frames : [];
  }

  function renderFramesStrip() {
    framesStripGrid.innerHTML = '';
    const frames = getActiveFramesList();
    if (frames.length === 0) {
      framesStripGrid.innerHTML = '<p class="text-muted">No individual frames loaded.</p>';
      return;
    }
    frames.forEach((frameUrl, idx) => {
      const card = document.createElement('div');
      card.className = 'frame-card';
      card.innerHTML = `
        <img src="${frameUrl}" alt="Frame ${idx + 1}">
        <span class="frame-label">Frame ${idx + 1} (${state.activePreviewDirection || 'S'})</span>
      `;
      framesStripGrid.appendChild(card);
    });
  }

  // --- Display Generated Asset & Preview Player ---
  function displayAsset(asset) {
    state.currentAsset = asset;
    state.fps = asset.fps || 8;
    playerFpsSlider.value = state.fps;
    playerFpsDisplay.textContent = state.fps;

    emptyState.style.display = 'none';
    activeFrameImg.style.display = 'block';

    // Directional suite setup
    if (asset.is_directional && asset.paths.directional_frames) {
      state.directionalFramesMap = asset.paths.directional_frames;
      const dirs = Object.keys(asset.paths.directional_frames);
      state.activePreviewDirection = dirs.includes('S') ? 'S' : dirs[0];

      if (playerDirectionBar && playerDirButtons) {
        playerDirectionBar.style.display = 'flex';
        playerDirButtons.innerHTML = '';
        dirs.forEach(d => {
          const b = document.createElement('button');
          b.className = `player-dir-btn ${d === state.activePreviewDirection ? 'active' : ''}`;
          b.textContent = d;
          b.title = DIR_DESCRIPTIONS[d] || d;
          b.addEventListener('click', () => {
            playerDirButtons.querySelectorAll('.player-dir-btn').forEach(btn => btn.classList.remove('active'));
            b.classList.add('active');
            state.activePreviewDirection = d;
            state.currentFrameIndex = 0;
            renderCurrentFrame();
            renderFramesStrip();
          });
          playerDirButtons.appendChild(b);
        });
      }
    } else {
      state.directionalFramesMap = null;
      if (playerDirectionBar) playerDirectionBar.style.display = 'none';
    }

    const frames = getActiveFramesList();
    totalFramesCountSpan.textContent = frames.length;
    state.currentFrameIndex = 0;
    renderCurrentFrame();

    // Export Card Links
    exportCard.style.display = 'block';
    downloadSpritesheet.href = asset.paths.spritesheet;
    downloadGif.href = asset.paths.preview_gif;
    downloadWebp.href = asset.paths.preview_webp;
    downloadMetadata.href = `/output/${asset.project}/${asset.rubrik}/${asset.asset_name}/metadata.json`;
    outputSavedPath.textContent = asset.paths.asset_folder;

    if (downloadNormal) {
      if (asset.paths.normal_map) {
        downloadNormal.href = asset.paths.normal_map;
        downloadNormal.style.display = 'inline-flex';
      } else {
        downloadNormal.style.display = 'none';
      }
    }
    if (downloadDepth) {
      if (asset.paths.depth_map) {
        downloadDepth.href = asset.paths.depth_map;
        downloadDepth.style.display = 'inline-flex';
      } else {
        downloadDepth.style.display = 'none';
      }
    }

    // Spritesheet Viewer Tab
    state.currentMapType = 'diffuse';
    mapPillBtns.forEach(p => p.classList.toggle('active', p.dataset.map === 'diffuse'));
    spritesheetFullImg.src = asset.paths.spritesheet;
    spritesheetFullImg.style.display = 'block';
    spritesheetEmpty.style.display = 'none';

    // Frames Strip Grid Tab
    renderFramesStrip();

    // Start playing animation
    startAnimation();
  }

  function renderCurrentFrame() {
    const frames = getActiveFramesList();
    if (frames.length === 0) return;

    activeFrameImg.src = frames[state.currentFrameIndex];
    currentFrameIdxSpan.textContent = state.currentFrameIndex + 1;
    totalFramesCountSpan.textContent = frames.length;

    // Onion Skinning (Ghost Frames)
    if (state.onionSkinEnabled && frames.length > 1) {
      const prevIdx = (state.currentFrameIndex - 1 + frames.length) % frames.length;
      const nextIdx = (state.currentFrameIndex + 1) % frames.length;

      onionFramePrev.src = frames[prevIdx];
      onionFramePrev.style.display = 'block';

      onionFrameNext.src = frames[nextIdx];
      onionFrameNext.style.display = 'block';
    } else {
      if (onionFramePrev) onionFramePrev.style.display = 'none';
      if (onionFrameNext) onionFrameNext.style.display = 'none';
    }
  }

  function startAnimation() {
    stopAnimation();
    state.isPlaying = true;
    btnPlayPause.textContent = '⏸️';
    const intervalMs = Math.max(20, Math.floor(1000 / state.fps));
    state.animationInterval = setInterval(() => {
      const frames = getActiveFramesList();
      if (frames.length === 0) return;
      state.currentFrameIndex = (state.currentFrameIndex + 1) % frames.length;
      renderCurrentFrame();
    }, intervalMs);
  }

  function stopAnimation() {
    state.isPlaying = false;
    btnPlayPause.textContent = '▶️';
    if (state.animationInterval) {
      clearInterval(state.animationInterval);
      state.animationInterval = null;
    }
  }

  btnPlayPause.addEventListener('click', () => {
    if (state.isPlaying) {
      stopAnimation();
    } else {
      startAnimation();
    }
  });

  btnStepPrev.addEventListener('click', () => {
    stopAnimation();
    const frames = getActiveFramesList();
    if (frames.length === 0) return;
    state.currentFrameIndex = (state.currentFrameIndex - 1 + frames.length) % frames.length;
    renderCurrentFrame();
  });

  btnStepNext.addEventListener('click', () => {
    stopAnimation();
    const frames = getActiveFramesList();
    if (frames.length === 0) return;
    state.currentFrameIndex = (state.currentFrameIndex + 1) % frames.length;
    renderCurrentFrame();
  });

  playerFpsSlider.addEventListener('input', (e) => {
    state.fps = parseInt(e.target.value, 10);
    playerFpsDisplay.textContent = state.fps;
    if (state.isPlaying) {
      startAnimation();
    }
  });

  // Onion Skinning Toggle
  if (btnToggleOnion) {
    btnToggleOnion.addEventListener('click', () => {
      state.onionSkinEnabled = !state.onionSkinEnabled;
      btnToggleOnion.classList.toggle('active', state.onionSkinEnabled);
      renderCurrentFrame();
      showToast(state.onionSkinEnabled ? '🧅 Onion Skinning Enabled (Ghost Frames)' : 'Onion Skinning Disabled');
    });
  }

  // Normal Map View Toggle
  if (btnToggleNormal) {
    btnToggleNormal.addEventListener('click', () => {
      if (!state.currentAsset || !state.currentAsset.paths.normal_map) {
        showToast('No normal map baked for this asset yet.');
        return;
      }
      state.normalMapPreview = !state.normalMapPreview;
      btnToggleNormal.classList.toggle('active', state.normalMapPreview);
      if (state.normalMapPreview) {
        activeFrameImg.style.filter = 'drop-shadow(0 0 8px rgba(130, 130, 255, 0.8)) hue-rotate(180deg) saturate(1.8)';
        showToast('🔮 2D Normal Map Shader Preview Active');
      } else {
        activeFrameImg.style.filter = 'none';
        showToast('Color (Diffuse) View Active');
      }
    });
  }

  // Spritesheet Map Switcher Pills
  mapPillBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (!state.currentAsset) return;
      mapPillBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const mapType = btn.dataset.map;
      state.currentMapType = mapType;
      const ts = Date.now();
      if (mapType === 'diffuse') {
        spritesheetFullImg.src = `${state.currentAsset.paths.spritesheet}?t=${ts}`;
      } else if (mapType === 'normal') {
        if (state.currentAsset.paths.normal_map) {
          spritesheetFullImg.src = `${state.currentAsset.paths.normal_map}?t=${ts}`;
        } else {
          showToast('Normal map not baked yet.');
        }
      } else if (mapType === 'depth') {
        if (state.currentAsset.paths.depth_map) {
          spritesheetFullImg.src = `${state.currentAsset.paths.depth_map}?t=${ts}`;
        } else {
          showToast('Depth map not baked yet.');
        }
      }
    });
  });

  // Chroma-Key Tool Handlers
  if (chromaToleranceSlider && chromaTolVal) {
    chromaToleranceSlider.addEventListener('input', (e) => {
      chromaTolVal.textContent = e.target.value;
    });
  }

  if (btnApplyChroma) {
    btnApplyChroma.addEventListener('click', async () => {
      if (!state.currentAsset || !state.currentAsset.paths.spritesheet) {
        showToast('No spritesheet loaded to apply background removal.');
        return;
      }
      btnApplyChroma.disabled = true;
      btnApplyChroma.textContent = '⏳ Processing...';
      try {
        const res = await fetch('/api/tools/chroma_key', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_url: state.currentAsset.paths.spritesheet,
            color: chromaColorPicker ? chromaColorPicker.value : null,
            tolerance: parseInt(chromaToleranceSlider.value, 10)
          })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('Background removed & normal maps updated!');
          const ts = Date.now();
          spritesheetFullImg.src = `${state.currentAsset.paths.spritesheet}?t=${ts}`;
          renderCurrentFrame();
        } else {
          showToast('Chroma key failed');
        }
      } catch (e) {
        showToast('Error applying chroma key');
      } finally {
        btnApplyChroma.disabled = false;
        btnApplyChroma.textContent = 'Remove BG';
      }
    });
  }

  if (btnRebakeMaps) {
    btnRebakeMaps.addEventListener('click', async () => {
      if (!state.currentAsset || !state.currentAsset.paths.spritesheet) {
        showToast('No spritesheet loaded.');
        return;
      }
      btnRebakeMaps.disabled = true;
      btnRebakeMaps.textContent = '⏳ Baking...';
      try {
        const res = await fetch('/api/tools/bake_maps', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_url: state.currentAsset.paths.spritesheet,
            strength: 2.0,
            invert_y: false
          })
        });
        const data = await res.json();
        if (data.status === 'success') {
          state.currentAsset.paths.normal_map = data.normal_map;
          state.currentAsset.paths.depth_map = data.depth_map;
          if (downloadNormal) {
            downloadNormal.href = data.normal_map;
            downloadNormal.style.display = 'inline-flex';
          }
          if (downloadDepth) {
            downloadDepth.href = data.depth_map;
            downloadDepth.style.display = 'inline-flex';
          }
          showToast('Normal Map & Depth Map baked successfully!');
        } else {
          showToast('Baking maps failed');
        }
      } catch (e) {
        showToast('Error baking maps');
      } finally {
        btnRebakeMaps.disabled = false;
        btnRebakeMaps.textContent = 'Bake Maps';
      }
    });
  }

  if (btnEyedropper) {
    btnEyedropper.addEventListener('click', async () => {
      if (window.EyeDropper) {
        try {
          const eyeDropper = new window.EyeDropper();
          const result = await eyeDropper.open();
          if (result && result.sRGBHex) {
            chromaColorPicker.value = result.sRGBHex;
            showToast(`Sampled color: ${result.sRGBHex}`);
          }
        } catch (e) {
          // cancelled
        }
      } else {
        showToast('Click anywhere on the preview frame to sample color');
        const pickHandler = (e) => {
          const canvas = document.createElement('canvas');
          canvas.width = activeFrameImg.naturalWidth || 64;
          canvas.height = activeFrameImg.naturalHeight || 64;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(activeFrameImg, 0, 0);
          const rect = activeFrameImg.getBoundingClientRect();
          const x = Math.floor((e.clientX - rect.left) / rect.width * canvas.width);
          const y = Math.floor((e.clientY - rect.top) / rect.height * canvas.height);
          try {
            const pixel = ctx.getImageData(x, y, 1, 1).data;
            const hex = '#' + ((1 << 24) + (pixel[0] << 16) + (pixel[1] << 8) + pixel[2]).toString(16).slice(1);
            chromaColorPicker.value = hex;
            showToast(`Sampled color: ${hex}`);
          } catch (err) {
            console.warn(err);
          }
          activeFrameImg.removeEventListener('click', pickHandler);
          activeFrameImg.style.cursor = 'default';
        };
        activeFrameImg.style.cursor = 'crosshair';
        activeFrameImg.addEventListener('click', pickHandler, { once: true });
      }
    });
  }

  // Zoom Controls
  zoomBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      zoomBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const z = btn.dataset.zoom;
      spriteContainer.className = `sprite-container zoom-${z}x`;
    });
  });

  btnToggleGrid.addEventListener('click', () => {
    spriteViewport.classList.toggle('checkerboard');
    btnToggleGrid.classList.toggle('active');
  });

  // Tab Navigation
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const tabId = btn.dataset.tab;
      document.getElementById(tabId).classList.add('active');

      if (tabId === 'tab-gallery') {
        loadGallery();
      }
    });
  });

  // Gallery
  async function loadGallery() {
    const proj = projectSelect.value;
    const rub = galleryRubrikFilter.value;
    try {
      const url = `/api/assets?project=${encodeURIComponent(proj)}${rub ? '&rubrik=' + encodeURIComponent(rub) : ''}`;
      const res = await fetch(url);
      const data = await res.json();
      galleryGrid.innerHTML = '';
      const list = data.assets || [];
      if (list.length === 0) {
        galleryGrid.innerHTML = '<p class="text-muted">No assets found in this project.</p>';
        return;
      }
      list.forEach(item => {
        const card = document.createElement('div');
        card.className = 'gallery-card';
        card.innerHTML = `
          <div class="gallery-thumb">
            <img src="${item.thumbnail_path}" alt="${item.asset_name}">
          </div>
          <span class="gallery-title">${item.asset_name}</span>
          <span class="gallery-sub">${item.rubrik} • ${item.metadata.perspective || '2D'}</span>
        `;
        galleryGrid.appendChild(card);
      });
    } catch (e) {
      galleryGrid.innerHTML = '<p class="text-muted">Error loading gallery.</p>';
    }
  }

  document.getElementById('btn-refresh-gallery').addEventListener('click', loadGallery);
  galleryRubrikFilter.addEventListener('change', loadGallery);
  btnRefreshStatus.addEventListener('click', checkServices);

  // Initial Boot
  loadConfig();
  checkServices();
  setInterval(checkServices, 30000);
  window.addEventListener('focus', checkServices);
});

