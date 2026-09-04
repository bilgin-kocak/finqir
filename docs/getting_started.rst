:orphan:

###############
Getting started
###############

Installation
============

FinQIR depends on Qiskit, which has its own
`installation instructions <https://quantum.cloud.ibm.com/docs/guides/install-qiskit>`__ detailing the
installation options and its supported environments/platforms. You should refer to
that first. Then the information here can be followed which focuses on the additional installation
specific to FinQIR.

.. tab-set::

    .. tab-item:: Start locally

        The simplest way to get started is to follow the installation guide for Qiskit `here <https://quantum.cloud.ibm.com/docs/guides/install-qiskit>`__

        In your virtual environment, where you installed Qiskit, install ``finqir`` as follows:

        .. code:: sh

            pip install finqir

        .. note::

            As FinQIR depends on Qiskit, you can though simply install it into your
            environment, as above, and pip will automatically install a compatible version of Qiskit
            if one is not already installed.

    .. tab-item:: Install from source

       Installing FinQIR from source allows you to access the most recently
       updated version under development instead of using the version in the Python Package
       Index (PyPI) repository. This will give you the ability to inspect and extend
       the latest version of the FinQIR code more efficiently.

       .. raw:: html

          <h2>Installing FinQIR from Source</h2>

       Using the same development environment that you installed Qiskit in you are ready to install
       FinQIR.

       1. Clone the FinQIR repository.

          .. code:: sh

             git clone https://github.com/bilgin-kocak/finqir.git

       2. Cloning the repository creates a local folder called ``finqir``.

          .. code:: sh

             cd finqir

       3. If you want to run tests or linting checks, install the developer requirements.

          .. code:: sh

             pip install -e ".[test,dev]"

       The editable installation means code changes do not require reinstalling
       the package.

----

Ready to get going?...
======================

.. raw:: html

   <div class="tutorials-callout-container">
      <div class="row">

.. qiskit-call-to-action-item::
   :description: Find out about FinQIR.
   :header: Dive into the tutorials
   :button_link:  ./tutorials/index.html
   :button_text: FinQIR tutorials

.. raw:: html

      </div>
   </div>


.. Hiding - Indices and tables
   :ref:`genindex`
   :ref:`modindex`
   :ref:`search`
