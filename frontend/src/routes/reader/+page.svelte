<script lang="ts">
	import { onMount } from 'svelte';
	import { appState } from '$lib/store.svelte';
	import Editor from '$lib/Editor.svelte';
	import 'pdfjs-dist/web/pdf_viewer.css';
	import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

	// API and Project states
	let projectId = $state('');
	let bookId = $state(''); // direct book read (no project)
	let isReadOnly = $state(false);
	let projectTitle = $state('Loading...');
	let isPublic = $state(true);
	let forkedFromId = $state<string | null>(null);
	let token = $state('');
	let noteContent = $state('');
	let commitMessage = $state('Updated notes');

	// Review states
	let reviews = $state<any[]>([]);
	let showReviewModal = $state(false);
	let reviewStatus = $state('approved');
	let reviewComments = $state('');
	let userRole = $state('student');

	// UI State
	let isEditorOpen = $state(false);
	let showHighlightToolbar = $state(false);
	let popupStyle = $state('');
	
	// Real PDF rendering state
	let viewerContainerRef = $state<HTMLDivElement | null>(null);
	let viewerRef = $state<HTMLDivElement | null>(null);
	let pdfViewer = $state<any>(null);
	let pdfjs = $state<any>(null);
	let pdfDoc = $state<any>(null);
	let bookDetails = $state<any>(null);
	let currentPage = $state(1);
	let totalPages = $state(1);
	let scale = $state(1.2);
	
	// Dynamic page text selection state
	let pageTextItems = $state<any[]>([]);
	
	// View Modes
	let viewMode = $state<'pdf' | 'text' | 'dual' | 'image'>('pdf');
	let isExtractingText = $state(false);
	let pageTextContent = $state('');
	let isPageExtracted = $state(false);
	let showAiConfigModal = $state(false);
	let showModelPickerModal = $state(false);
	let showBatchExtractModal = $state(false);
	let batchExtractStart = $state(1);
	let batchExtractEnd = $state(1);
	let activeAiConfig = $state<any>(null);

	// Image fallback intersection observer
	let imageObserver: IntersectionObserver;
	let imageContainerRef = $state<HTMLElement | null>(null);

	function observeImage(node: HTMLElement) {
		if (imageObserver) {
			imageObserver.observe(node);
		}
		return {
			destroy() {
				if (imageObserver) {
					imageObserver.unobserve(node);
				}
			}
		};
	}

	onMount(() => {
		// Only run on client
		if (typeof window === 'undefined') return;
		
		// Setup intersection observer for native image infinite scrolling
		imageObserver = new IntersectionObserver((entries) => {
			for (const entry of entries) {
				if (entry.isIntersecting) {
					const pageNum = parseInt(entry.target.getAttribute('data-page') || '1', 10);
					if (currentPage !== pageNum) {
						currentPage = pageNum;
						extractTextForPage(currentPage);
					}
				}
			}
		}, {
			root: imageContainerRef,
			rootMargin: '0px',
			threshold: 0.5 // trigger when 50% of the image is visible
		});
	});

	let isRtl = $derived(appState.language === 'ar');

	onMount(async () => {
		appState.language = localStorage.getItem('appLanguage') || 'en';
		token = localStorage.getItem('token') || '';
		
		// Parse URL params
		const params = new URLSearchParams(window.location.search);
		projectId = params.get('project_id') || '';
		bookId = params.get('book_id') || '';
		
		// Decode user role from JWT token if available
		if (token) {
			try {
				const base64Url = token.split('.')[1];
				const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
				const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
					return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
				}).join(''));
				const payload = JSON.parse(jsonPayload);
				userRole = payload.role || 'student';
			} catch (e) {
				console.error("Error decoding token:", e);
			}
		}

		// Dynamically load pdfjs-dist and viewer to prevent SSR issues
		try {
			pdfjs = await import('pdfjs-dist');
			const pdfjsViewerLib = await import('pdfjs-dist/web/pdf_viewer.mjs');
			pdfjsViewer = pdfjsViewerLib; // Assign to state			
			// We no longer manually render pages to a single canvas here since we rely on pdfViewer for scrolling
			// If we switch to image mode, we just scroll to the right image
			if (viewMode === 'image') {
				const imgEl = document.getElementById(`native-img-page-${currentPage}`);
				if (imgEl) {
					imgEl.scrollIntoView({ behavior: 'smooth' });
				}
			}
			pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;
		} catch (err) {
			console.error("Failed to load PDF.js client-side module:", err);
		}

		if (bookId && !projectId) {
			// Direct read-only mode — load book without a project
			isReadOnly = true;
			projectTitle = 'Loading book...';
			await fetchBookDetails(bookId);
		} else if (projectId) {
			await fetchProjectDetails();
			await fetchProjectHeadCommit();
			await fetchProjectReviews();
		}
	});

	async function fetchProjectDetails() {
		try {
			const res = await fetch(`http://localhost:8000/api/projects/${projectId}`);
			if (res.ok) {
				const data = await res.json();
				projectTitle = data.title;
				isPublic = data.is_public;
				forkedFromId = data.forked_from_id;
				if (data.document_id) {
					await fetchBookDetails(data.document_id);
				}
			}
		} catch (err) {
			console.error("Error fetching project:", err);
		}
	}

	async function fetchBookDetails(bookId: string) {
		console.log("Fetching book details for ID:", bookId);
		try {
			const res = await fetch(`http://localhost:8000/api/books/${bookId}`);
			if (res.ok) {
				bookDetails = await res.json();
				console.log("Book details loaded:", bookDetails);
				// Update title to book name when in read-only mode
				if (isReadOnly) {
					projectTitle = bookDetails.title || 'Book Reader';
				}
				if (bookDetails.file_path) {
					// Properly encode path segments
					const parts = bookDetails.file_path.split('/');
					const encodedPath = parts.map((p: string) => encodeURIComponent(p)).join('/');
					const encodedUrl = `http://localhost:8000/${encodedPath}`;
					console.log("Loading PDF from encoded URL:", encodedUrl);
					await loadPdf(encodedUrl);
				}
			}
		} catch (err) {
			console.error("Error fetching book details:", err);
		}
	}

	async function loadPdf(url: string) {
		if (!pdfjs || !pdfjsViewer) {
			console.error("PDF.js library is not loaded yet!");
			return;
		}
		try {
			const pdfjsDistUrl = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/`;
			const loadingTask = pdfjs.getDocument({
				url: url,
				cMapUrl: pdfjsDistUrl + 'cmaps/',
				cMapPacked: true,
				standardFontDataUrl: pdfjsDistUrl + 'standard_fonts/',
				wasmUrl: pdfjsDistUrl + 'wasm/'
			});
			pdfDoc = await loadingTask.promise;
			totalPages = pdfDoc.numPages;
			
			// Initialize PDFViewer
			if (viewerContainerRef && viewerRef) {
				const eventBus = new pdfjsViewer.EventBus();
				const linkService = new pdfjsViewer.PDFLinkService({ eventBus });
				pdfViewer = new pdfjsViewer.PDFViewer({
					container: viewerContainerRef,
					viewer: viewerRef,
					eventBus,
					linkService
				});
				linkService.setViewer(pdfViewer);
				linkService.setDocument(pdfDoc, null);
				pdfViewer.setDocument(pdfDoc);

				eventBus.on('pagechanging', (evt: any) => {
					currentPage = evt.pageNumber;
					extractTextForPage(currentPage);
				});
			}
			
			currentPage = 1;
			await extractTextForPage(1);
		} catch (err) {
			console.error("Error loading PDF document:", err);
		}
	}

	let extractTask: any = null;
	async function extractTextForPage(pageNum: number) {
		if (!bookDetails) return;
		try {
			isExtractingText = true;
			const res = await fetch(`http://localhost:8000/api/books/${bookDetails.id}/pages/${pageNum}`);
			if (res.ok) {
				const data = await res.json();
				if (data.extracted) {
					isPageExtracted = true;
					pageTextContent = data.content;
				} else {
					isPageExtracted = false;
					pageTextContent = '';
				}
			}
		} catch (err) {
			console.error("Error fetching text:", err);
			isPageExtracted = false;
		} finally {
			isExtractingText = false;
		}
	}

	async function checkAiConfig() {
		try {
			const res = await fetch('http://localhost:8000/api/ai/config', {
				headers: { 'Authorization': `Bearer ${token}` }
			});
			if (res.ok) {
				const data = await res.json();
				if (data.configured) {
					activeAiConfig = data;
					showModelPickerModal = true;
				} else {
					showAiConfigModal = true;
				}
			}
		} catch (err) {
			console.error("Error checking AI config:", err);
			showAiConfigModal = true;
		}
	}

	async function saveDummyAiConfig(type: 'online' | 'local') {
		try {
			const res = await fetch('http://localhost:8000/api/ai/config', {
				method: 'POST',
				headers: { 
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({
					model_type: type,
					provider: type === 'online' ? 'gemini' : 'ollama',
					api_key: 'dummy-key'
				})
			});
			if (res.ok) {
				showAiConfigModal = false;
				checkAiConfig();
			}
		} catch(err) {
			console.error("Failed to save config", err);
		}
	}

	async function triggerExtraction(start: number, end: number) {
		showModelPickerModal = false;
		showBatchExtractModal = false;
		if (!bookDetails) return;
		try {
			isExtractingText = true;
			const res = await fetch(`http://localhost:8000/api/books/${bookDetails.id}/extract`, {
				method: 'POST',
				headers: { 
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({ start_page: start, end_page: end })
			});
			if (res.ok) {
				// Re-fetch current page
				extractTextForPage(currentPage);
			}
		} catch (err) {
			console.error("Error extracting text:", err);
		} finally {
			isExtractingText = false;
		}
	}

	// React to page or scale modifications
	$effect(() => {
		if (pdfDoc && currentPage && scale) {
			// Extract text if not already on that page's text
			// Actually extractTextForPage is called by eventBus pagechanging!
		}
	});

	function prevPage() {
		if (pdfViewer && currentPage > 1) {
			pdfViewer.currentPageNumber = currentPage - 1;
		}
	}

	function nextPage() {
		if (pdfViewer && currentPage < totalPages) {
			pdfViewer.currentPageNumber = currentPage + 1;
		}
	}

	function handlePageInput(e: Event) {
		const target = e.target as HTMLInputElement;
		const val = parseInt(target.value);
		if (pdfViewer && !isNaN(val) && val >= 1 && val <= totalPages) {
			pdfViewer.currentPageNumber = val;
		} else {
			target.value = currentPage.toString();
		}
	}

	function setSpreadMode(mode: 'NONE' | 'ODD' | 'EVEN') {
		if (!pdfViewer) return;
		switch(mode) {
			case 'NONE': pdfViewer.spreadMode = 0; break;
			case 'ODD': pdfViewer.spreadMode = 1; break;
			case 'EVEN': pdfViewer.spreadMode = 2; break;
		}
	}

	async function fetchProjectHeadCommit() {
		try {
			const res = await fetch(`http://localhost:8000/api/projects/${projectId}/branches/main/head`);
			if (res.ok) {
				const data = await res.json();
				noteContent = data.content || '';
			}
		} catch (err) {
			console.error("Error fetching head commit:", err);
		}
	}

	async function fetchProjectReviews() {
		try {
			const res = await fetch(`http://localhost:8000/api/reviews/project/${projectId}`);
			if (res.ok) {
				reviews = await res.json();
			}
		} catch (err) {
			console.error("Error fetching reviews:", err);
		}
	}

	async function handleCommit() {
		if (!projectId || !token) {
			alert("Please log in to save changes.");
			return;
		}
		try {
			const res = await fetch(`http://localhost:8000/api/projects/${projectId}/commit`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({
					commit_message: commitMessage,
					content: noteContent,
					branch_name: 'main'
				})
			});
			if (res.ok) {
				alert("Commit saved successfully!");
				commitMessage = "Updated notes"; // reset
			} else {
				const err = await res.json();
				alert(`Failed to commit: ${err.detail}`);
			}
		} catch (err) {
			console.error("Error committing:", err);
		}
	}

	async function handleFork() {
		if (!projectId || !token) {
			alert("Please log in to fork projects!");
			return;
		}
		try {
			const res = await fetch(`http://localhost:8000/api/projects/${projectId}/fork`, {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${token}`
				}
			});
			if (res.ok) {
				const data = await res.json();
				alert(`Forked successfully! Redirecting to new project.`);
				window.location.href = `/reader?project_id=${data.id}`;
			} else {
				const err = await res.json();
				alert(`Failed to fork: ${err.detail}`);
			}
		} catch (err) {
			console.error("Error forking project:", err);
		}
	}

	async function submitReview() {
		if (!projectId || !token) return;
		try {
			// Find head commit ID first from the main branch
			const headRes = await fetch(`http://localhost:8000/api/projects/${projectId}/branches/main/head`);
			if (!headRes.ok) {
				alert("Could not retrieve head commit to review.");
				return;
			}
			const headData = await headRes.json();
			const commitId = headData.id;

			const res = await fetch(`http://localhost:8000/api/reviews`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({
					project_id: projectId,
					commit_id: commitId,
					status: reviewStatus,
					comments: reviewComments
				})
			});
			if (res.ok) {
				showReviewModal = false;
				reviewComments = '';
				alert("Review submitted successfully!");
				await fetchProjectReviews();
			} else {
				const err = await res.json();
				alert(`Failed to submit review: ${err.detail}`);
			}
		} catch (err) {
			console.error("Error submitting review:", err);
		}
	}

	function toggleEditor() {
		isEditorOpen = !isEditorOpen;
	}

	function handleSelection() {
		const selection = window.getSelection();
		if (selection && selection.toString().trim() !== '') {
			// Get exact coordinates of the highlight for the popup
			const rect = selection.getRangeAt(0).getBoundingClientRect();
			popupStyle = `top: ${rect.top - 40}px; left: ${rect.left + (rect.width / 2) - 50}px;`;
			showHighlightToolbar = true;
		} else {
			showHighlightToolbar = false;
		}
	}

	function createLinkedNote(color: string) {
		showHighlightToolbar = false;
		isEditorOpen = true;
		console.log('Created note anchor with color:', color);
	}
</script>

<svelte:head>
	<title>{projectTitle} - Reader</title>
</svelte:head>

<!-- dir flips based on global language -->
<div class="h-screen w-full bg-gray-100 flex flex-col font-sans overflow-hidden" dir={isRtl ? 'rtl' : 'ltr'}>

	<!-- Top Reader Toolbar flips layout based on language -->
	<header class="h-14 bg-white border-b border-gray-200 flex items-center px-4 shrink-0 z-20 shadow-sm" dir={isRtl ? 'rtl' : 'ltr'}>

		<!-- back arrow + title -->
		<div class="flex items-center gap-3 min-w-0 flex-1">
			<a href={isReadOnly ? '/books' : '/my-notes'}
			   class="shrink-0 text-gray-500 hover:text-gray-900 transition {isRtl ? 'rotate-180' : ''}"
			   title={isReadOnly ? 'Back to Library' : 'Back to Dashboard'}>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
			</a>
			<div class="min-w-0">
				<h1 class="text-sm font-bold text-gray-800 truncate" dir={isRtl ? 'rtl' : 'ltr'}>{projectTitle}</h1>
				<p class="text-xs font-medium {isReadOnly ? 'text-amber-600' : 'text-emerald-600'}">
					{#if isReadOnly}
						👁 View Only
					{:else if isRtl}
						🕌 عربي · main · {isPublic ? 'عام' : 'خاص'}
					{:else}
						Branch: main · {isPublic ? 'Public' : 'Private'}{forkedFromId ? ' · Forked' : ''}
					{/if}
				</p>
			</div>
		</div>

		<!-- CENTER: page navigation -->
		<div class="flex items-center gap-1 bg-gray-100 p-1 rounded-lg mx-4 shrink-0">
			<button onclick={prevPage} disabled={currentPage === 1} class="w-8 h-8 flex items-center justify-center hover:bg-white rounded-md shadow-sm text-gray-600 disabled:opacity-40 transition">
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
			</button>
			<div class="flex items-center gap-1 px-1">
				<input type="number" value={currentPage} onchange={handlePageInput} min="1" max={totalPages} class="w-12 h-6 text-center text-xs font-mono text-gray-900 bg-white border border-gray-300 rounded shadow-inner [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none" />
				<span class="text-xs font-mono text-gray-500 select-none">/ {totalPages}</span>
			</div>
			<button onclick={nextPage} disabled={currentPage === totalPages} class="w-8 h-8 flex items-center justify-center hover:bg-white rounded-md shadow-sm text-gray-600 disabled:opacity-40 transition">
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
			</button>
		</div>

		<!-- RIGHT: actions + Open Notebook always at far right -->
		<div class="flex items-center gap-2 shrink-0">
			<!-- Layout Toggle (Spread Mode) -->
			{#if viewMode === 'pdf' || viewMode === 'dual'}
				<div class="hidden md:flex items-center bg-gray-100 rounded-lg p-1 shrink-0" dir="ltr">
					<button onclick={() => setSpreadMode('NONE')} class="px-2 py-1 text-xs font-bold rounded-md transition text-gray-500 hover:text-gray-800 hover:bg-white" title="Single Page Layout">Single</button>
					<button onclick={() => setSpreadMode('ODD')} class="px-2 py-1 text-xs font-bold rounded-md transition text-gray-500 hover:text-gray-800 hover:bg-white" title="Dual Page Layout">Spread</button>
				</div>
			{/if}

			<!-- View Mode Toggle -->
			<div class="hidden sm:flex items-center bg-gray-100 rounded-lg p-1 mx-1 shrink-0" dir="ltr">
				<button onclick={() => viewMode = 'pdf'} class="px-2.5 py-1 text-xs font-bold rounded-md transition {viewMode === 'pdf' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'}" title="Browser PDF Engine">PDF</button>
				<button onclick={() => viewMode = 'image'} class="px-2.5 py-1 text-xs font-bold rounded-md transition {viewMode === 'image' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'}" title="Native Image Fallback">Image</button>
				{#if !isReadOnly}
					<button onclick={() => viewMode = 'dual'} class="px-2.5 py-1 text-xs font-bold rounded-md transition {viewMode === 'dual' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'}">Dual</button>
					<button onclick={() => viewMode = 'text'} class="px-2.5 py-1 text-xs font-bold rounded-md transition {viewMode === 'text' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'}">Text</button>
				{/if}
			</div>

			{#if isReadOnly}
				<a href="/books" class="text-xs bg-emerald-700 hover:bg-emerald-800 text-white px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 ml-2">
					<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
					Start Study Project
				</a>
			{:else}
				
				<!-- Loading State -->
				{#if isExtractingText}
					<div class="flex items-center gap-1.5 text-emerald-600 text-xs font-bold mr-2">
						<svg class="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
						<span class="hidden md:inline">Reading...</span>
					</div>
				{/if}

				<!-- Secondary actions (reviews, fork) -->
				{#if reviews.some(r => r.status === 'approved')}
					<span class="text-xs font-bold bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full flex items-center gap-1">
						<svg class="w-3 h-3 text-emerald-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M2.166 4.9L9.03 1.7a1 1 0 01.937 0l6.865 3.2A1 1 0 0117.4 5.8v4.45a7.994 7.994 0 01-4.04 6.94l-3 1.69a1 1 0 01-.72 0l-3-1.69A7.994 7.994 0 012.6 10.25V5.8a1 1 0 01.566-.9zM8 11a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L9 8.586 7.707 7.293a1 1 0 00-1.414 1.414l2 2z" clip-rule="evenodd"></path></svg>
						Approved
					</span>
				{/if}
				{#if ['scholar', 'teacher', 'admin'].includes(userRole)}
					<button onclick={() => showReviewModal = true} class="text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-lg font-bold transition">
						Review
					</button>
				{/if}
				<button onclick={handleFork} class="text-gray-400 hover:text-emerald-700 flex items-center gap-1 transition" title="Fork Project">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path></svg>
				</button>
				<button onclick={() => showBatchExtractModal = true} class="text-gray-400 hover:text-emerald-700 transition" title="Extract Range">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
				</button>
				<!-- Divider -->
				<div class="w-px h-6 bg-gray-200 mx-1"></div>
				<!-- Open Notebook — always rightmost -->
				<button onclick={toggleEditor}
					class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-bold shadow transition
						{isEditorOpen ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' : 'bg-gray-800 text-white hover:bg-gray-900'}"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
					{isEditorOpen ? 'Close' : 'Notebook'}
				</button>
			{/if}
		</div>
	</header>

	<!-- Main Workspace Area -->
	<div class="flex-1 flex overflow-hidden relative">
		
		<!-- Center/Left: PDF Canvas Viewer or Native Image -->
		<!-- dir=ltr always for PDF canvas coordinates; Arabic text inside PDF renders via PDF.js itself -->
		<div class="flex-1 bg-gray-200 relative transition-all duration-300 {viewMode === 'text' ? 'hidden' : ''}" dir="ltr" onmouseup={handleSelection} role="presentation">
			{#if bookDetails && bookDetails.file_path}
				<div bind:this={imageContainerRef} class="absolute inset-0 overflow-auto w-full h-full flex-col items-center bg-gray-900 p-8 gap-8 {viewMode === 'image' ? 'flex' : 'hidden'}"
					 onscroll={() => { /* scrolling handled by IntersectionObserver */ }}>
					<!-- Native images rendered by backend PyMuPDF -->
					{#each Array(totalPages) as _, i}
						<img 
							id={`native-img-page-${i + 1}`}
							data-page={i + 1}
							src={`http://localhost:8000/api/books/${bookDetails.id}/render/${i + 1}`} 
							alt={`Page ${i + 1}`} 
							loading="lazy"
							class="max-w-full lg:max-w-3xl xl:max-w-4xl shadow-2xl bg-white min-h-[600px] w-full object-contain transition-opacity duration-300" 
							use:observeImage
						/>
					{/each}
				</div>

				<div bind:this={viewerContainerRef} class="absolute inset-0 overflow-auto w-full h-full {viewMode === 'image' ? 'hidden' : 'block'}">
					<div bind:this={viewerRef} class="pdfViewer"></div>
				</div>
			{:else}
				<!-- Placeholder for citation/thematic study session -->
				<div class="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 text-gray-400 p-8 text-center">
					<svg class="w-16 h-16 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
					<p class="font-bold text-gray-600 text-sm">Thematic Study Session</p>
					<p class="text-xs max-w-xs mt-1">This project focuses on thematic notes referencing multiple sources without a single PDF document upload.</p>
				</div>
			{/if}
		</div>

		<!-- Center/Right: Text Viewer -->
		{#if viewMode === 'text' || viewMode === 'dual'}
			<div class="flex-1 overflow-auto bg-white relative p-8 transition-all duration-300 {viewMode === 'dual' ? 'border-l border-gray-200' : ''}" dir={isRtl ? 'rtl' : 'ltr'}>
				<div class="max-w-3xl mx-auto">
					{#if isExtractingText}
						<div class="flex flex-col items-center justify-center h-full text-gray-400 mt-20">
							<svg class="animate-spin w-8 h-8 mb-4 text-emerald-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
							<p>Extracting text...</p>
						</div>
					{:else if !isPageExtracted}
						<div class="flex flex-col items-center justify-center h-full text-center mt-20 p-8 bg-gray-50 rounded-xl border border-gray-200">
							<svg class="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
							<h3 class="text-xl font-bold text-gray-700 mb-2">Text Not Extracted</h3>
							<p class="text-gray-500 mb-6 max-w-md">This page is not converted yet to text, will you convert it or see the pdf normally (but you can't highlight or give notes)?</p>
							<div class="flex gap-4">
								<button onclick={() => viewMode = 'pdf'} class="px-5 py-2 text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 font-medium transition">View Normal PDF</button>
								<button onclick={checkAiConfig} class="px-5 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 font-medium transition shadow">Convert Page</button>
							</div>
						</div>
					{:else}
						<h2 class="text-xl font-bold mb-6 text-gray-800 border-b pb-2 flex items-center justify-between">
							<span>Page {currentPage} Text</span>
							<span class="text-xs font-normal text-gray-400 bg-emerald-100 text-emerald-800 px-2 py-1 rounded">Extracted by AI</span>
						</h2>
						<div class="prose prose-emerald max-w-none text-lg leading-relaxed whitespace-pre-wrap {isRtl ? 'text-right font-arabic' : 'text-left font-serif'} text-gray-700">
							{pageTextContent}
						</div>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Contextual Highlight Popup Toolbar -->
		{#if showHighlightToolbar}
			<div class="fixed bg-gray-900 text-white rounded-lg shadow-2xl p-2 flex gap-3 z-50 transition-all border border-gray-700 items-center" style={popupStyle}>
				<span class="text-xs font-bold px-1 text-gray-300 border-r border-gray-700 pr-2">Add Note</span>
				<button onclick={() => createLinkedNote('yellow')} class="w-5 h-5 rounded-full bg-yellow-400 hover:scale-125 transition shadow-inner" title="General"></button>
				<button onclick={() => createLinkedNote('green')} class="w-5 h-5 rounded-full bg-emerald-400 hover:scale-125 transition shadow-inner" title="Aqidah"></button>
				<button onclick={() => createLinkedNote('blue')} class="w-5 h-5 rounded-full bg-blue-400 hover:scale-125 transition shadow-inner" title="Fiqh"></button>
			</div>
		{/if}

		<!-- Notebook Panel — slides from RIGHT for LTR, LEFT for RTL -->
		<aside
			class="absolute top-0 h-full w-full md:w-96 bg-white shadow-2xl z-30 transition-transform duration-300 ease-in-out
				{isRtl ? 'left-0 border-r border-gray-200' : 'right-0 border-l border-gray-200'}
				{isEditorOpen
					? 'translate-x-0'
					: isRtl ? '-translate-x-full' : 'translate-x-full'}"
			dir={isRtl ? 'rtl' : 'ltr'}
		>
			<div class="h-full flex flex-col">
				<!-- Panel Header -->
				<div class="h-14 border-b border-gray-100 flex items-center justify-between px-4 bg-gray-50 shrink-0" dir={isRtl ? 'rtl' : 'ltr'}>
					<h3 class="font-bold text-gray-800 flex items-center gap-2">
						<svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
						{isRtl ? 'دفتر الملاحظات' : 'My Notebook'}
					</h3>
					<button onclick={toggleEditor} class="text-gray-400 hover:text-gray-700 transition">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
					</button>
				</div>
				
				<!-- Editor Content -->
				<div class="flex-1 overflow-y-auto p-4 bg-gray-50 flex flex-col gap-6" dir={isRtl ? 'rtl' : 'ltr'}>
					
					<!-- Smart Reference Editor -->
					<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
						<Editor bind:noteContent={noteContent} />
					</div>
					
					<!-- Commit Form -->
					<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
						<h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Save Snapshot (Commit)</h4>
						<input type="text" bind:value={commitMessage} placeholder="Commit message (e.g. Updated notes)" class="w-full p-2 border border-gray-300 rounded text-sm mb-3 outline-none focus:ring-1 focus:ring-emerald-500" />
						<div class="flex justify-end gap-2">
							<button onclick={handleCommit} class="w-full py-2 text-sm font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded transition shadow">
								Commit & Save
							</button>
						</div>
					</div>

					<!-- Scholarly Reviews List -->
					<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
						<h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Scholarly Reviews</h4>
						{#if reviews.length === 0}
							<p class="text-xs text-gray-400">No reviews submitted yet.</p>
						{:else}
							<div class="space-y-3">
								{#each reviews as review}
									<div class="p-3 border rounded text-xs {review.status === 'approved' ? 'bg-emerald-50 border-emerald-100' : 'bg-yellow-50 border-yellow-100'}">
										<div class="flex justify-between items-center mb-1">
											<span class="font-bold text-gray-800">@{review.scholar_username}</span>
											<span class="font-mono text-gray-400">{new Date(review.timestamp).toLocaleDateString()}</span>
										</div>
										<p class="text-gray-700 italic">"{review.comments}"</p>
										<div class="mt-2 text-right">
											<span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase {review.status === 'approved' ? 'bg-emerald-200 text-emerald-800' : 'bg-yellow-200 text-yellow-800'}">
												{review.status}
											</span>
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>

				</div>
			</div>
		</aside>
	</div>

	<!-- AI Config Modal -->
	{#if showAiConfigModal}
		<div class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4">
			<div class="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 text-center">
				<h3 class="text-xl font-bold text-gray-800 mb-2">AI Not Configured</h3>
				<p class="text-gray-600 text-sm mb-6">You need to configure an AI model before you can extract text from this document.</p>
				<div class="space-y-3">
					<button onclick={() => saveDummyAiConfig('online')} class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-emerald-50 hover:border-emerald-200 transition text-left group">
						<div>
							<div class="font-bold text-gray-800 group-hover:text-emerald-700">Cloud API (Gemini/OpenAI)</div>
							<div class="text-xs text-gray-500">Fast, high accuracy OCR</div>
						</div>
						<svg class="w-5 h-5 text-gray-400 group-hover:text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
					</button>
					<button onclick={() => saveDummyAiConfig('local')} class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-emerald-50 hover:border-emerald-200 transition text-left group">
						<div>
							<div class="font-bold text-gray-800 group-hover:text-emerald-700">Local Model (Ollama)</div>
							<div class="text-xs text-gray-500">Private, runs on your device</div>
						</div>
						<svg class="w-5 h-5 text-gray-400 group-hover:text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
					</button>
				</div>
				<button onclick={() => showAiConfigModal = false} class="mt-6 text-gray-500 hover:text-gray-800 text-sm font-medium">Cancel</button>
			</div>
		</div>
	{/if}

	<!-- Model Picker Modal (when multiple models are available) -->
	{#if showModelPickerModal}
		<div class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4">
			<div class="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6 text-center">
				<h3 class="text-xl font-bold text-gray-800 mb-2">Convert Text</h3>
				<p class="text-gray-600 text-sm mb-6">Extracting page {currentPage} using <span class="font-bold text-emerald-600">{activeAiConfig?.provider} ({activeAiConfig?.model_type})</span></p>
				<div class="flex gap-3 justify-center">
					<button onclick={() => showModelPickerModal = false} class="px-4 py-2 border border-gray-300 rounded text-gray-600 hover:bg-gray-50">Cancel</button>
					<button onclick={() => triggerExtraction(currentPage, currentPage)} class="px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 font-medium">Start Extraction</button>
				</div>
				<!-- Settings link -->
				<button onclick={() => { showModelPickerModal = false; showAiConfigModal = true; }} class="mt-4 text-xs text-emerald-600 hover:underline">Change AI Model Settings</button>
			</div>
		</div>
	{/if}

	<!-- Batch Extract Modal -->
	{#if showBatchExtractModal}
		<div class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4">
			<div class="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6">
				<h3 class="text-xl font-bold text-gray-800 mb-4">Batch Convert Pages</h3>
				<div class="flex gap-4 mb-6">
					<div class="flex-1">
						<label class="block text-xs font-bold text-gray-600 mb-1">Start Page</label>
						<input type="number" bind:value={batchExtractStart} min="1" max={totalPages} class="w-full px-3 py-2 border border-gray-300 rounded focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" />
					</div>
					<div class="flex-1">
						<label class="block text-xs font-bold text-gray-600 mb-1">End Page</label>
						<input type="number" bind:value={batchExtractEnd} min="1" max={totalPages} class="w-full px-3 py-2 border border-gray-300 rounded focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" />
					</div>
				</div>
				<div class="flex justify-end gap-3">
					<button onclick={() => showBatchExtractModal = false} class="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium">Cancel</button>
					<button onclick={() => triggerExtraction(batchExtractStart, batchExtractEnd)} class="px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 font-medium">Extract Range</button>
				</div>
			</div>
		</div>
	{/if}
</div>

<!-- Scholar Review Modal -->
{#if showReviewModal}
	<div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
		<div class="bg-white w-full max-w-md rounded-xl shadow-2xl p-6">
			<div class="flex justify-between items-center mb-4 border-b pb-2">
				<h3 class="font-bold text-gray-800 text-lg">Add Scholar Review</h3>
				<button onclick={() => showReviewModal = false} class="text-gray-400 hover:text-gray-700">
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
				</button>
			</div>
			<div class="flex flex-col gap-4">
				<div>
					<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Decision</label>
					<select bind:value={reviewStatus} class="w-full p-2 border rounded outline-none focus:ring-1 focus:ring-emerald-500">
						<option value="approved">Approve Notes</option>
						<option value="needs_work">Request Changes</option>
					</select>
				</div>
				<div>
					<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Comments</label>
					<textarea bind:value={reviewComments} rows="4" placeholder="Feedback or corrections..." class="w-full p-2 border rounded outline-none focus:ring-1 focus:ring-emerald-500 text-sm"></textarea>
				</div>
				<button onclick={submitReview} class="bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded font-bold transition">
					Submit Review
				</button>
			</div>
		</div>
	</div>
{/if}
