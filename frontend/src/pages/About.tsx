import { YaleLogo } from '../components/YaleLogo'

export function About() {
  return (
    <div className="page">
      <div style={{ display: 'flex', gap: '2.5rem', alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div className="prose">
          <h1>About Us</h1>

          <h2>Yale University</h2>
          <p>
            Yale was founded in 1701 by a group of Connecticut ministers as the Collegiate
            School, meeting first in Killingworth and then Saybrook before settling in New
            Haven in 1716. It took its present name in 1718 in recognition of a gift from
            Elihu Yale, a merchant and administrator of the East India Company. The motto
            on the shield — <em>Lux et Veritas</em>, light and truth — dates from the
            early eighteenth century.
          </p>
          <p>
            Yale awarded the first doctorate in the United States in 1861, admitted women
            to Yale College in 1969, and today enrolls roughly 14,000 students across
            Yale College, the Graduate School and twelve professional schools. Its Gothic
            residential colleges, the Beinecke Rare Book &amp; Manuscript Library and the
            Yale Bowl are as much a part of the New Haven skyline as the university itself.
          </p>
          <p>
            The Game — Yale against Harvard, played every November since 1875 — remains
            the oldest rivalry in college football, and the single busiest week of the
            year for anyone selling Yale apparel.
          </p>

          <h2>Campus Customs</h2>
          <p>
            Campus Customs started in a basement on Elm Street with one heat press and a
            standing order for intramural shirts. The founders were undergraduates who
            could not find Yale merchandise that looked like something a student would
            actually wear, so they started printing it themselves.
          </p>

          <div className="timeline">
            <div>
              <span>2016</span>
              <h3>One press, one dorm room</h3>
              <p className="muted">
                A single heat press and a run of intramural shirts for the residential
                college leagues.
              </p>
            </div>
            <div>
              <span>2018</span>
              <h3>The Broadway storefront</h3>
              <p className="muted">
                A shop near the Yale Bookstore, and the first full line of hoodies and
                crewnecks in Yale blue.
              </p>
            </div>
            <div>
              <span>2021</span>
              <h3>Varsity partnerships</h3>
              <p className="muted">
                Licensed team wordmarks for baseball, crew, hockey and a dozen other
                programs — the left-chest designs still in the catalogue today.
              </p>
            </div>
            <div>
              <span>2025</span>
              <h3>Over 100 styles</h3>
              <p className="muted">
                Tees, crewnecks, quarter-zips, fleece and bomber jackets, every one of
                them stocked XS through XXL.
              </p>
            </div>
          </div>

          <p>
            Everything is printed in New Haven, usually within 48 hours of the order. The
            whole catalogue lives on this site, and the assistant in the corner can read
            all of it — ask it what is left in your size.
          </p>
        </div>

        <aside className="about-side">
          <div className="about-logo">
            <YaleLogo size={160} tone="dark" />
          </div>

          <div className="side-card">
            <h3>At a glance</h3>
            <dl className="facts">
              <div>
                <dt>Founded</dt>
                <dd>Yale, 1701 · Campus Customs, 2016</dd>
              </div>
              <div>
                <dt>Where</dt>
                <dd>Broadway, New Haven, CT</dd>
              </div>
              <div>
                <dt>Printed</dt>
                <dd>In house, usually within 48 hours</dd>
              </div>
              <div>
                <dt>Range</dt>
                <dd>100+ styles, every one XS–XXL</dd>
              </div>
            </dl>
          </div>

          <div className="side-card">
            <h3>Visit the shop</h3>
            <p>
              33 Broadway, New Haven, CT 06511
              <br />
              Mon–Sat, 10am–7pm
            </p>
            <p className="muted">
              hello@campuscustoms.yale.edu
              <br />
              (203) 555-0142
            </p>
          </div>

          <div className="side-card accent">
            <h3>Harvard–Yale</h3>
            <p>
              The Game comes to New Haven this November. Rivalry tees and
              crewnecks sell out first — the assistant in the corner can tell you
              what is still in your size.
            </p>
          </div>
        </aside>
      </div>
    </div>
  )
}
