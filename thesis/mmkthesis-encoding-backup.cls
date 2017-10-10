%
%
%    Copyright (C) 2013-2015 Philipp Tiefenbacher (philipp.tiefenbacher@tum.de)
%    Institute for Human-Machine Communication
%    Technische Universität München, Germany
%    http://www.mmk.ei.tum.de/personen/mitarbeiter/philipp-tiefenbacher/
%
%    This code is free software: you can redistribute it and/or modify
%    it under the terms of the GNU General Public License as published by
%    the Free Software Foundation, version 3 of the License.
%
%    This code is distributed in the hope that it will be useful,
%    but WITHOUT ANY WARRANTY; without even the implied warranty of
%    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%    GNU General Public License for more details.
%
%    You should have received a copy of the GNU General Public License
%    along with this code.  If not, see <http://www.gnu.org/licenses/>.
%
%    This is a small class with the typical MMK thesis appearance: 
%     * It is kept as simple as possible
%     * No sophisticated confusing chaos-class
%     * It is based on some classes available in the internet (Stanfords suthesis, etc.) 
%       and the works of my colleagues Benedikt Hörnler, Marc Al-Hames, and Stephan Schwärzler. 
%


% Identify class 
\NeedsTeXFormat{LaTeX2e}
% Nice figures
\ProvidesClass{mmkthesis}


% Based on the class book
\LoadClass[12pt]{book}

% The geometry of the pages is 1cm for binding and then a simple 12 division
% ToDo: Doublecheck that
\usepackage[a4paper,BCOR10mm,headinclude,DIV14]{typearea}
% Until subsubsection there are numbers; not any further
\setcounter{secnumdepth}{4}                                            

% The typical MMK PhD thesis chapter title with a nice thick line
% with numbering
\renewcommand{\@makechapterhead}[1]{
  \vspace*{60\p@}%
  {\parindent \z@ \raggedright \normalfont
    \vspace{5pt}%
    \ifnum \c@secnumdepth >\m@ne
      \Huge \textbf{\thechapter}             % Chapter number
      \par\nobreak
      \vspace{5pt}%
    \fi
    \interlinepenalty\@M
    \thicklines
    \hrule height 0.5mm                      % Nice thick line, invented by Marc, I think
    \flushright{\huge \textbf{#1}\par}       % Title with huge font size, right-aligned
    \nobreak
    \vskip 40\p@
  }}

% The typical MMK PhD thesis chapter title with a nice thick line
% without numbering
\renewcommand{\@makeschapterhead}[1]{
  \vspace*{60\p@}%
  {\parindent \z@ \raggedright \normalfont
    \vspace{5pt}%
    \ifnum \c@secnumdepth >\m@ne
      \Huge $\textbf{\phantom{\thechapter}}$  % No chapter number
      \par\nobreak
      \vspace{5pt}%
    \fi
    \interlinepenalty\@M
      \thicklines
      \hrule height 0.5mm                     % Nice thick line
      \flushright{\huge \textbf{#1}\par}      % Title with huge font size, right-aligned
    \nobreak
    \vskip 40\p@
  }}

% Adaptation of the header 
\usepackage{fancyhdr}                  
\pagestyle{fancy} 
\fancyfoot{}                                    % Clears all footer fields
\fancyfoot[C]{\thepage}                                    
\renewcommand{\chaptermark}[1]{                 % On the left page the chapter
  \markboth{\thechapter.\ #1}{}}
\renewcommand{\sectionmark}[1]{             
  \markright{\thesection.\ #1}}         
\fancyhead{}                                    % Clears all header fields
\fancyhead[LE,LO]{\nouppercase{\leftmark}}      % Chapter at the left 
\renewcommand{\headrulewidth}{0.3pt}            % Beautiful line below the header
% Pages after a chapter should not have a header
\makeatletter
\def\cleardoublepage{\clearpage\if@twoside \ifodd\c@page\else
    \hbox{}
    \thispagestyle{empty}
    \newpage
    \if@twocolumn\hbox{}\newpage\fi\fi\fi}
\makeatother

\usepackage{chngpage}                            
% Defining the title page
\renewcommand{\titlepage}{                      % Typical MMK title page with all the official information
    \thispagestyle{empty}
    \begin{center}
	\begin{figure}
		\includegraphics[scale=1]{ei_logo} 
		\hfill
		\includegraphics[scale=1]{tum_logo}
		\vspace{1.0cm}	
	\end{figure}
        {\huge \textbf{\mmktypeofwork}}\\
		\vspace{1.25cm}
		\large{\MakeUppercase{Institute for Human-Machine Communication}\\
		\vspace{0.15cm}
        \MakeUppercase{Technische Universit\"at M\"unchen}\\
		\vspace{0.15cm}
        Univ.-Prof.\ Dr.-Ing.\ habil.\ G.\ Rigoll}\\
        \vspace{2.0cm}        
		{\LARGE \textbf{\mmktitle}}\\
        \vspace{1.25cm}
		\large{\mmkauthor}
    \end{center}
    \vfill
    \begin{tabbing}
        Advisor: \qquad \qquad \=\mmkadvisor\\
        \\\\
        Started on: \>\startedon\\
        Handed in on: \>\handedinon
    \end{tabbing}
}

% End of mmkthesis class
\endinput
