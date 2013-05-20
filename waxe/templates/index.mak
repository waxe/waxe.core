<%inherit file="base.mak" />

% if error_msg:
  Error: ${error_msg|n}
% endif

<section id="section-content">
  <ul class="breadcrumb navbar-fixed-top" style="top:40px; z-index: 999;">
  % if breadcrumb:
    ${breadcrumb|n}
  % endif
  </ul>

  <div class="content">
  % if content:
    ${content|n}
  % endif
  </div>
</section>
