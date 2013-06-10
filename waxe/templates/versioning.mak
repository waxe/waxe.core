<div class="ui-layout-center">
% if files_data:
  <ul>
  % for status, label_class, f, link in files_data:
     <li>
	  <span class="label ${label_class}">${status}</span>
	  <a data-href="${link}">
       ${f}
	  </a>
     </li>
  % endfor
  </ul>
% endif
</div>
