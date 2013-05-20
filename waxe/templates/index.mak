<%inherit file="base.mak" />

<section id="section-content">
  <ul class="breadcrumb navbar-fixed-top" style="top:40px; z-index: 999;">
	% if breadcrumb:
	  ${breadcrumb|n}
	% endif
  </ul>

  <div class="content">
    ${content|n}
  </div>
</section>
